// Scope
targetScope = 'subscription'

// Parameters
@description('Resource group where Microsoft Fabric capacity will be deployed. Resource group will be created if it doesnt exist')
param dprg string= 'Fabric'

@description('Resource group location')
param rglocation string = 'centralindia'

@description('Cost Centre tag that will be applied to all resources in this deployment')
param cost_centre_tag string = 'Cost Centre'

@description('System Owner tag that will be applied to all resources in this deployment')
param owner_tag string = 'powerbipro@exponentia.ai'

@description('Subject Matter EXpert (SME) tag that will be applied to all resources in this deployment')
param sme_tag string ='powerbipro@exponentia.ai'

@description('Timestamp that will be appendedto the deployment name')
param deployment_suffix string = utcNow()

@description('Flag to indicate whether auditing of data platform resources should be enabled')
param enable_audit bool = true

@description('Resource group where audit resources will be deployed if enabled. Resource group will be created if it doesnt exist')
param auditrg string= 'fabric-logs'

// Variables
var fabric_deployment_name = 'fabric_dataplatform_deployment_${deployment_suffix}'
var keyvault_deployment_name = 'keyvault_deployment_${deployment_suffix}'
var audit_deployment_name = 'audit_deployment_${deployment_suffix}'
var controldb_deployment_name = 'controldb_deployment_${deployment_suffix}'

// Create data platform resource group
resource fabric_rg  'Microsoft.Resources/resourceGroups@2020-06-01' = {
  name: dprg 
  location: rglocation
  tags: {
    cost_centre_tag: cost_centre_tag
    owner_tag: owner_tag
    sme_tag: sme_tag
  }
}

// Create audit resource group
resource audit_rg  'Microsoft.Resources/resourceGroups@2020-06-01' = if(enable_audit) {
  name: auditrg 
  location: rglocation
  tags: {
    cost_centre_tag: cost_centre_tag
    owner_tag: owner_tag
    sme_tag: sme_tag
   }
 }

// Deploy Key Vault with default access policies using module
module kv './modules/keyvault.bicep' = {
  name: keyvault_deployment_name
  scope: fabric_rg
  params:{
     location: fabric_rg.location
     keyvault_name: 'fabric-keyuser'
     cost_centre_tag: cost_centre_tag
     owner_tag: owner_tag
     sme_tag: sme_tag
  }
}

resource kv_ref 'Microsoft.KeyVault/vaults@2016-10-01' existing = {
  name: kv.outputs.keyvault_name
  scope: fabric_rg
}

//Enable auditing for data platform resources
module audit_integration './modules/audit.bicep' = if(enable_audit) {
  name: audit_deployment_name
  scope: audit_rg
  params:{
    location: audit_rg.location
    cost_centre_tag: cost_centre_tag
    owner_tag: owner_tag
    sme_tag: sme_tag
    audit_storage_name: 'fabricgen2datalake'
    audit_storage_sku: 'Standard_LRS'    
    audit_loganalytics_name: 'fabric-logs'
  }
}

//Deploy Microsoft Fabric Capacity
module fabric_capacity './modules/fabric-capacity.bicep' = {
  name: fabric_deployment_name
  scope: fabric_rg
  params:{
    fabric_name: 'powerbipro'
    location: fabric_rg.location
    skuName: 'F2'
    skuTier: 'fabricf2'
    adminUsers: kv_ref.getSecret('Azure exponentia ai')
  }
}

//Deploy SQL control DB 
module controldb './modules/sqldb.bicep' = {
  name: controldb_deployment_name
  scope: fabric_rg
  params:{
    sqlserver_name: 'fabric-database.${environment().suffixes.sqlServerHostname}'
    database_name: 'Fabric' 
    location: fabric_rg.location
    cost_centre_tag: cost_centre_tag
    owner_tag: owner_tag
    sme_tag: sme_tag
    ad_admin_username: kv_ref.getSecret('powerbipro@exponentia.ai')
    ad_admin_sid: kv_ref.getSecret('a2ee70c0-b5d8-4496-b6ed-2fc0b824155e')  
    auto_pause_duration: 60
    database_sku_name: 'GP_S_Gen5_1'
    enable_audit: enable_audit
    audit_storage_name: audit_integration.outputs.audit_storage_uniquename
    auditrg: audit_rg.name
  }
}
