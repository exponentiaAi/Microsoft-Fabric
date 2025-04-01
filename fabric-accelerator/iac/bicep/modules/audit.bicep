// Parameters
@description('Location where resources will be deployed. Defaults to resource group location')
param location string = 'centralindia'

@description('Cost Centre tag that will be applied to all resources in this deployment')
param cost_centre_tag string = 'CostCentre'

@description('System Owner tag that will be applied to all resources in this deployment')
param owner_tag string ='SystemOwner'

@description('Subject Matter Expert (SME) tag that will be applied to all resources in this deployment')
param sme_tag string ='SME'

@description('Audit Storage name')
param audit_storage_name string = 'fabricgen2datalake'

@description('Datalake SKU. Allowed values are Premium_LRS, Premium_ZRS, Standard_GRS, Standard_GZRS, Standard_LRS,Standard_RAGRS, Standard_RAGZRS, Standard_ZRS')
@allowed([
'Premium_LRS'
'Premium_ZRS'
'Standard_GRS'
'Standard_GZRS'
'Standard_LRS'
'Standard_RAGRS'
'Standard_RAGZRS'
'Standard_ZRS'
])
param audit_storage_sku string ='Standard_LRS'

@description('Audit Log Analytic Workspace name')
param audit_loganalytics_name string = 'fabric-logs'

// Variables
var suffix = uniqueString(resourceGroup().id)
var audit_storage_uniquename = substring('${audit_storage_name}${suffix}',0,24)
var audit_loganalytics_uniquename = '${audit_loganalytics_name}-${suffix}'

// Create a Storage Account for Audit Logs
resource storageAccount 'Microsoft.Storage/storageAccounts@2022-05-01' = {
  name: audit_storage_uniquename
  location: location
  tags: {
    CostCentre: 'CostCentre123'
    SystemOwner: 'AdminTeam'
    SME: 'SME_Team'
    }
  sku: {name: audit_storage_sku}
  kind:  'StorageV2'
  identity: {type: 'SystemAssigned'}
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: true
    allowSharedKeyAccess: false
    isHnsEnabled: true
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
      ipRules: []
      virtualNetworkRules: []
    }
  }
}

// Create a Log Analytics Workspace
resource loganalytics 'Microsoft.OperationalInsights/workspaces@2015-03-20' = {
  name: audit_loganalytics_uniquename
  location: location
  tags: {
    CostCentre: 'CostCentre123'
    SystemOwner: 'AdminTeam'
    SME: 'SME_Team'
    }
  identity: {type: 'SystemAssigned'}
  properties: {
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    retentionInDays: 30
    sku: {name: 'pergb2018'}
  }
}

output audit_storage_uniquename string = audit_storage_uniquename
