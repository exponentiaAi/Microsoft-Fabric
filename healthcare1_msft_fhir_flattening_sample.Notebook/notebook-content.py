# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "ba421746-f565-4458-bc9f-aac23cb360ea",
# META       "default_lakehouse_name": "healthcare1_msft_silver",
# META       "default_lakehouse_workspace_id": "ff86597a-b979-43a6-96a6-6784918d1e48"
# META     },
# META     "environment": {
# META       "environmentId": "fd0309f6-3c63-8465-455a-7449f2cb7fb6",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# MARKDOWN ********************

# ##### WARNING
# The following notebook is intended to be read only. Please do not modify the contents of this notebook.


# MARKDOWN ********************

# #### Overview
# 
# ##### Parsing String Extensions
# 
# Extensions are child elements that represent additional information and can be present in every element in a resource. The exact definition and use of extensions can be found in [FHIR Extension Element](https://www.hl7.org/fhir/extensibility.html#extension). 
# 
# For example, for the patient resource, there is no clear element to define race information. However, if this information were to be added for the patient, extensions would need to be utilized. This is an example of an extension used for the race information:
# 
# ```
# {
#     "extension": [
#         {
#             "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
#             "extension": [
#                 {
#                     "url": "ombCategory",
#                     "valueCoding": {
#                         "system": "urn:oid:2.16.840.1.113883.6.238",
#                         "code": "2106-3",
#                         "display": "White"
#                     }
#                 },
#                 {
#                     "url": "text",
#                     "valueString": "White"
#                 }
#             ]
#         }
#     ]
# }
# ```
# 
# Currently extensions are supported as strings within our schema. This notebook provides examples of how to access this extension data and utilize it within a dataframe. There are 2 avenues for utilizing the data within extensions: using a provided parse_extension utility or using the provided extension schema to parse the extension. The parse_extension utility is used to retrieve specific fields from the full string extension. In addition, the full extension schema has been provided and can be used to parse the entire string extension.
# To utilize this notebook bronze and silver ingestion will have to be completed prior as this leverages the silver database in the samples
# 
# Structure of the notebook:
# 1. **Load data and set up**: We begin by loading the necessary config details that you can specify.
# 2. **Parsing extension using parse_extension utility**: We utilize the parse extension utility to parse an extension and retrieve individual fields
# 3. **Parsing extension using provided extension schema**: We utilize the provided extension schema to parse the entire string extension
# 
# Key Parameters for parse_extension utility:
# - `extension`: The full string extension column
# - `urlList`: The comma delimited list of url's (Each comma separated url will represent a nested level depth)
# - `value`: The value at the specified url that should be retrieved
# - `field`: comma delimited list of field(s) in the case the value is a complex type. If multiple fields are selected they will be concatenated with the '<->' token
# 
#   
# 
# _For more information and detailed steps see the [Healthcare data solutions Documentation](https://aka.ms/hds-doc)_

# MARKDOWN ********************

# ##### Configuration management and setup
# The following cells will setup and manage configurations for the Healthcare data solutions:

# CELL ********************

%run healthcare1_msft_config_notebook

# METADATA ********************

# META {
# META   "frozen": false,
# META   "editable": false
# META }

# CELL ********************

%run healthcare1_msft_config_notebook {"enable_spark_setup" : true, "enable_packages_mount" : false}

# METADATA ********************

# META {
# META   "frozen": false,
# META   "editable": false
# META }

# MARKDOWN ********************

# ##### Parsing extension using parse_extension utility
# After setting up the prerequisites, we utilize the parse_extension utility to parse the extension and retrieve values
# 
# The below example shows the extraction of 3 values from the extension field in the Patient resource utilizing the Patient resource:
# - p_life_years: This is an extension value for url "http://synthetichealth.github.io/synthea/disability-adjusted-life-years". Since this is a decimal value, as defined in the FHIR extension, we will cast the value as decimal after retrieving the value.
# - p_birthplace_city: This is an extension value for url "http://hl7.org/fhir/StructureDefinition/patient-birthPlace". The "valueAddress' value is a struct and therefore the specific field(s) need to be retrieved through the field parameter. In this case, the "city" field is being retrieved. Since this is a string value, no casting will need to be done after retrieval.
# - p_ethnicity_standard: This is an extension value that is nested within another extension. The base extension is at url "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity". After retrieving the base extension, the nested extension is at url "ombCategory". The resulting url will be "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity,ombCategory". The "valueCoding" value is a struct and therefore the specific field(s) need to be retrieved through the field parameter. In this case, multiple fields are being retrieved: system and code. When multiple fields are retrieved, they are concatenated together with the `<->` token.

# MARKDOWN ********************

# Retrieve Silver Lakehouse ID from Parameter Service

# CELL ********************

from microsoft.fabric.hls.hds.utils.parameter_service import ParameterService
from microsoft.fabric.hls.hds.global_constants.global_constants import GlobalConstants as GC

parameter_service = ParameterService(
    spark,
    workspace_name=workspace_name,
    admin_lakehouse_name=administration_database_name,
    one_lake_endpoint=one_lake_endpoint
)

silver_database_name = parameter_service.get_foundation_config_value(GC.SILVER_LAKEHOUSE_ID_KEY)

# METADATA ********************

# META {
# META   "frozen": false,
# META   "editable": false
# META }

# MARKDOWN ********************

# This example shows the utilization of spark sql statement to retrieve the 3 values

# CELL ********************

from microsoft.fabric.hls.hds.utils.extension_parser import ExtensionParser

ExtensionParser.register(spark)
result_df = spark.sql(f"select *, id as o_id, msftModifiedDatetime as o_modified_date,\
    cast(parse_extension(extension, 'http://synthetichealth.github.io/synthea/disability-adjusted-life-years', 'valueDecimal', '') as float) as p_life_years, \
    parse_extension(extension, 'http://hl7.org/fhir/StructureDefinition/patient-birthPlace', 'valueAddress', 'city') as p_birthplace_city, \
    parse_extension(extension, 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity,ombCategory', 'valueCoding', 'system,code') as p_ethnicity_standard \
    from `{silver_database_name}`.`patient`")
display(result_df)

# METADATA ********************

# META {
# META   "frozen": false,
# META   "editable": false
# META }

# MARKDOWN ********************

# This example shows the utilization of the utility with pyspark to retrieve the 3 values

# CELL ********************

import json
from pyspark.sql.functions import lit, col, udf
from microsoft.fabric.hls.hds.utils.extension_parser import ExtensionParser

parse_extension = udf(ExtensionParser.parse_extension)
query = f"SELECT * FROM `{silver_database_name}`.`patient`"
result_df = spark.sql(query)

result_df = result_df.withColumn("p_life_years", parse_extension(col("extension"), lit('http://synthetichealth.github.io/synthea/disability-adjusted-life-years'), lit('valueDecimal'), lit('')).cast("float"))
result_df = result_df.withColumn("p_birthplace_city", parse_extension(col("extension"), lit('http://hl7.org/fhir/StructureDefinition/patient-birthPlace'), lit('valueAddress'), lit('city')))
result_df = result_df.withColumn("p_ethnicity_standard", parse_extension(col("extension"), lit('http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity,ombCategory'), lit('valueCoding'), lit('system,code')))
display(result_df)

# METADATA ********************

# META {
# META   "frozen": false,
# META   "editable": false
# META }

# MARKDOWN ********************

# The dataframe created above can be saved to the table with the below snippet

# CELL ********************

new_table_name = 'updatedpatient1'
result_df.write.mode("overwrite").saveAsTable(f"`{silver_database_name}`.`{new_table_name}`")

# METADATA ********************

# META {
# META   "frozen": false,
# META   "editable": false
# META }

# MARKDOWN ********************

# The newly created fields can be viewed and queried as follows

# CELL ********************

query = f"SELECT p_life_years, p_birthplace_city, p_ethnicity_standard FROM `{silver_database_name}`.`{new_table_name}`"
updated_patient_df = spark.sql(query)
display(updated_patient_df)

# METADATA ********************

# META {
# META   "frozen": false,
# META   "editable": false
# META }

# MARKDOWN ********************

# #### Parsing extension using provided extension schema
# In addition, the full extension schema has been provided and can be used to parse the entire string extension. This will create a full schematized extension column

# CELL ********************

import json
from pyspark.sql import types as T
from pyspark.sql.functions import from_json, col, udf

schema_path = f'{data_manager_config_path}/_internal/fhir4/extension_support/extensionschema.avsc'
extension_schema_content = spark.sparkContext.wholeTextFiles(schema_path).collect()[0][1]

extension_java_schema_type = spark.\
    _jvm.org.apache.spark.sql.avro.SchemaConverters.toSqlType(
        spark._jvm.org.apache.avro.Schema.Parser().parse                    
            (extension_schema_content) 
        )

extension_json_schema = json.loads(extension_java_schema_type.dataType().json())
extension_schema = T.StructType.fromJson(extension_json_schema)
schema = T.ArrayType(extension_schema)

query = f"SELECT * FROM `{silver_database_name}`.`patient`"
result_df = spark.sql(query)

result_df = result_df.withColumn("extension", from_json(col("extension"), schema))
display(result_df)

# METADATA ********************

# META {
# META   "frozen": false,
# META   "editable": false
# META }

# MARKDOWN ********************

# The dataframe created above can be saved to the table with the below snippet 

# CELL ********************

new_table_name = 'updatedpatient2'
result_df.write.mode("overwrite").saveAsTable(f"`{silver_database_name}`.`{new_table_name}`")

# METADATA ********************

# META {
# META   "frozen": false,
# META   "editable": false
# META }

# MARKDOWN ********************

# The same fields retrieved via the parse_extension utility above can now be retrieved using sql statement below:

# CELL ********************

query = f"select case when array_contains(extension.url, 'http://synthetichealth.github.io/synthea/disability-adjusted-life-years') then extension[array_position(extension.url, 'http://synthetichealth.github.io/synthea/disability-adjusted-life-years')-1].valueDecimal else NULL end as p_life_years, case when array_contains(extension.url, 'http://hl7.org/fhir/StructureDefinition/patient-birthPlace') then extension[array_position(extension.url, 'http://hl7.org/fhir/StructureDefinition/patient-birthPlace')-1].valueAddress.city else NULL end as p_birthplace_city, case when array_contains(extension.url, 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity') then concat_ws('<->', extension[array_position(extension.url, 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity')-1].extension[0].valueCoding.system, extension[array_position(extension.url, 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity')-1].extension[0].valueCoding.code) else NULL end as p_ethnicity_standard from `{silver_database_name}`.`{new_table_name}`"
new_df = spark.sql(query)
display(new_df)

# METADATA ********************

# META {
# META   "frozen": false,
# META   "editable": false
# META }
