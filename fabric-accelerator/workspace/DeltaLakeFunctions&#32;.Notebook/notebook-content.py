# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "",
# META       "default_lakehouse_workspace_id": ""
# META     }
# META   }
# META }

# MARKDOWN ********************

# ### Spark session configuration
# This cell sets Spark session settings to enable _Verti-Parquet_ and _Optimize on Write_.

# CELL ********************

from delta.tables import *
import json

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
spark.conf.set("spark.sql.parquet.vorder.enabled", "true")
spark.conf.set("spark.microsoft.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.microsoft.delta.optimizeWrite.binSize", "1073741824")
spark.conf.set('spark.ms.autotune.queryTuning.enabled', 'true')

#Low shuffle for untouched rows during MERGE
spark.conf.set("spark.microsoft.delta.merge.lowShuffle.enabled", "true")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # readFile()
# Reads a data file from Lakehouse and returns as Spark dataframe


# CELL ********************

def readFile(container, folder, file, colSeparator=None, headerFlag=None):
  # ##########################################################################################################################  
  # Function: readFile
  # Reads a data file from Lakehouse and returns as spark dataframe
  # 
  # Parameters:
  # container = Container of Lakehouse. Default value 'Files'
  # folder = Folder within container where data file resides. E.g 'raw-bronze/wwi/Sales/Orders/2013-01'
  # file = File name of data file including and file extension. E.g 'Sales_Orders_2013-01-01_000000.parquet'
  # colSeparator = Column separator for text files. Default value None
  # headerFlag = boolean flag to indicate whether the text file has a header or not. Default value None
  # 
  # Returns:
  # A dataframe of the data file
  # ##########################################################################################################################    
    assert container is not None, "container not provided"   
    assert folder is not None, "folder not provided"
    assert file is not None, "file not provided"

    relativePath =   container + '/' + folder +'/' + file

    if ".csv" in file or ".txt" in file:
        df = spark.read.csv(path=relativePath, sep=colSeparator, header=headerFlag, inferSchema="true")
    elif ".parquet" in file:
        df = spark.read.parquet(relativePath)
    elif ".json" in file:
        df = spark.read.json(relativePath, multiLine= True)
    elif ".orc" in file:
        df = spark.read.orc(relativePath)
    else:
        df = spark.read.format("csv").load(relativePath)
  
    df =df.dropDuplicates()
    return df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # insertDelta()
# Inserts a dataframe to delta lake table. Creates a table with the schema of dataframe if the table doesn't already exist

# CELL ********************

def insertDelta (df, tableName, writeMode="append"):
  # ##########################################################################################################################  
  # Function: insertDelta
  # Inserts a dataframe to delta lake table. Creates a table with the schema of dataframe if the table doesn't already exist
  # 
  # Parameters:
  # df = Input dataframe
  # tableName = Target tableName in current lakehouse
  # mode = write mode. Valid values are "append", "overwrite". Default value "append"
  # 
  # Returns:
  # Json containing operational metrics.This is useful to get information like number of records inserted/updated.
  # E.g payload
  # {'numOutputRows': '4432', 'numOutputBytes': '87157', 'numFiles': '1'}
  # ##########################################################################################################################  
    validMode =[ "append", "overwrite"]
    assert writeMode in validMode, "Invalid mode specified"

    # Creating a delta table with schema name not supported at the time of writing this code, so replacing schema name with "_". To be commented out when this
    #feature is available
    tableName = tableName.replace(".","_")
    
    #Get delta table reference
    DeltaTable.createIfNotExists(spark).tableName(tableName).addColumns(df.schema).execute()
    deltaTable = DeltaTable.forName(spark,tableName)
    tableName =deltaTable.detail()
    tableName =deltaTable.detail().select("location").first()[0].split("/")[-1] #get last "/" substring from location attribute of delta table
    assert tableName is not None, "Delta table does not exist"
    
    df.write.format("delta").mode(writeMode).saveAsTable(tableName)
    
    stats = deltaTable.history(1).select("OperationMetrics").first()[0]
    print(stats)

    return stats

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # upsertDelta()
# Upserts a dataframe to delta lake table. Inserts record if they don't exist, updates existing if the version is newer than existing

# CELL ********************

def upsertDelta(df,tableName,keyColumns,watermarkColumn=None):
  # ##########################################################################################################################################   
  # Function: upsertDelta
  # Upserts a dataframe to delta lake table. Inserts record if they don't exist, updates existing if the version is newer than existing
  # 
  # Parameters:
  # df = Input dataframe
  # tableName = Target tableName in current lakehouse
  # mode = write mode. Valid values are "append", "overwrite". Default value "append"
  # 
  # Returns:
  # Json containing operational metrics.This is useful to get information like number of records inserted/updated.
  # E.g payload
  #     {'numOutputRows': '4432', 'numTargetRowsInserted': '0', 'numTargetFilesAdded': '1', 
  #     'numTargetFilesRemoved': '1', 'executionTimeMs': '2898', 'unmodifiedRewriteTimeMs': '606',
  #      'numTargetRowsCopied': '0', 'rewriteTimeMs': '921', 'numTargetRowsUpdated': '4432', 'numTargetRowsDeleted': '0',
  #      'scanTimeMs': '1615', 'numSourceRows': '4432', 'numTargetChangeFilesAdded': '0'}
  # ##########################################################################################################################################   

    # Creating a delta table with schema name not supported at the time of writing this code, so replacing schema name with "_". To be commented out when this
    #feature is available
    tableName = tableName.replace(".","_")

    #Get target table reference
    DeltaTable.createIfNotExists(spark).tableName(tableName).addColumns(df.schema).execute()
    target = DeltaTable.forName(spark,tableName)
    assert target is not None, "Target delta lake table does not exist"

    keyColumnsList = keyColumns.split("|")
   
    #Merge Condition
    joinCond=""
    for keyCol in keyColumnsList:
        joinCond = joinCond + "target." + keyCol + " = source." + keyCol +" and "

    remove = "and"
    reverse_remove = remove[::-1]
    joinCond = joinCond[::-1].replace(reverse_remove,"",1)[::-1]

    if watermarkColumn is not None:
        joinCond = joinCond + " and target." + watermarkColumn + " <= source." + watermarkColumn
    
    # Column mappings for insert and update
    mapCols =""
    for col in df.columns:
        mapCols = mapCols + '"' + col + '":' + ' "' + 'source.' + col + '" ,'

    remove = ","
    reverse_remove = remove[::-1]
    mapCols = mapCols[::-1].replace(reverse_remove,"",1)[::-1]

    #Convert Insert and Update Expression in to Dict
    updateStatement = json.loads("{"+mapCols+"}")
    insertStatement = json.loads("{"+mapCols+"}")

    (target.alias("target")
            .merge( df.alias('source'), joinCond)
            .whenMatchedUpdate(set = updateStatement)
            .whenNotMatchedInsert(values = insertStatement)
            .execute()
     )   

    # print(updateStatement)
    stats = target.history(1).select("OperationMetrics").first()[0]
    print(stats)

    return stats

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # optimizeDelta()
# Compacts small files and removed unused files beyond default retention period for a Delta Table

# CELL ********************

def optimizeDelta(tableName):
  # ##########################################################################################################################################   
  # Function: optimizeDelta
  # Function that implements the compaction of small files for Delta Tables https://docs.delta.io/latest/optimizations-oss.html#language-python
  # Also removes unused files beyond default retention period
  # 
  # Parameters:
  # tableName = Delta lake tableName in current lakehouse
  # 
  # Returns:
  # None
  # ##########################################################################################################################################   
    # Creating a delta table with schema name not supported at the time of writing this code, so replacing schema name with "_". To be commented out when this
    #feature is available
    tableName = tableName.replace(".","_")

    deltaTable = DeltaTable.forName(spark,tableName)
    assert deltaTable is not None, "Delta lake table does not exist"
    deltaTable.optimize().executeCompaction()
    deltaTable.vacuum()
    return

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# df = readFile("Files","raw-bronze/wwi/Sales/Orders/2013-01","Sales_Orders_2013-01-01_000000.parquet")
# display(df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# upsertDelta(df,"sales_orders","OrderID|CustomerID","LastEditedWhen")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# insertDelta (df, "sales_orders", "append")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# optimizeDelta("silver_sales_customertransactions")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
