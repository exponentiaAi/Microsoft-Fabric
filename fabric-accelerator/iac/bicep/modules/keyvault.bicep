// Parameters
@description('Location where resources will be deployed. Defaults to resource group location')
param location string = resourceGroup().location

@description('Cost Centre tag that will be applied to all resources in this deployment')
param cost_centre_tag string

@description('System Owner tag that will be applied to all resources in this deployment')
param owner_tag string

@description('Subject Matter Expert (SME) tag that will be applied to all resources in this deployment')
param sme_tag string

@description('Key Vault name')
param keyvault_name string = 'fabric-keyuser'

// @description('Purview Account name')
// param purview_account_name string = 'fabric-purview'

// @description('Resource group of Purview Account')
// param purviewrg string = 'fabric-purview'

// @description('Flag to indicate whether to enable integration of data platform resources with either an existing or new Purview resource')
// param enable_purview bool = false

// Variables
var suffix = uniqueString(resourceGroup().id)
// var keyvault_uniquename = '${keyvault_name}${suffix}'
var truncatedSuffix = take(suffix, 10)  // Limit the suffix to 10 characters
var keyvault_uniquename = '${keyvault_name}${truncatedSuffix}'

// Create Key Vault
resource keyvault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyvault_uniquename
  location: location
  tags: {
    CostCentre: cost_centre_tag
    Owner: owner_tag
    SME: sme_tag
  }
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enabledForDeployment: true
    enabledForDiskEncryption: true
    enabledForTemplateDeployment: true
    accessPolicies: [
      { tenantId: subscription().tenantId
        objectId: '8e0c3f69-ed67-4374-bad3-00925cc2a0ea'
        permissions: {secrets: ['list','get','set','Delete','Recover','Backup','Restore']}
      }
      { tenantId: subscription().tenantId
        objectId: '5d2bf1c7-0d3e-41dd-b2d3-b28745352812'
        permissions: {secrets: ['list','get','set','Delete','Recover','Backup','Restore']}
      }
      { tenantId: subscription().tenantId
        objectId: 'a2ee70c0-b5d8-4496-b6ed-2fc0b824155e' //replace by powerbipro objectId
        permissions: {secrets: ['list','get','set','Delete','Recover','Backup','Restore']}
      }
    ]
  }
}

// Create Key Vault Access Policies for Purview
// resource existing_purview_account 'Microsoft.Purview/accounts@2021-07-01' existing = if(enable_purview) {
//   name: purview_account_name
//   scope: resourceGroup(purviewrg)
// }

// resource this_keyvault_accesspolicy 'Microsoft.KeyVault/vaults/accessPolicies@2022-07-01' = if(enable_purview) {
//   name: 'add'
//   parent: keyvault
//   properties: {
//     accessPolicies: [
//       { tenantId: subscription().tenantId
//         objectId: existing_purview_account.identity.principalId
//         permissions: { secrets: ['list','get']}
//       }
//     ]
//   }
// }

output keyvault_name string = keyvault.name
