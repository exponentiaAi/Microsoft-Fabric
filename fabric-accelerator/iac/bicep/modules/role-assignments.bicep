targetScope = 'resourceGroup'

@description('Managed Identity of the resource being granted permissions')
param principalId string

@description('Flag to grant Storage Blob Data Reader role to the storage account')
param grant_reader bool = true

@description('Flag to grant Storage Blob Data Contributor role to the storage account')
param grant_contributor bool = true

//In-built role definition for storage account
@description('This is the built-in Storage Blob Contributor role.')
resource sbdcRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: subscription()
  name: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}

@description('This is the built-in Storage Blob Reader role.')
resource sbdrRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: subscription()
  name: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
}

//Grant Storage Blob Data Contributor role to resource
resource grant_sbdc_role 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = if (grant_contributor) {
  name: guid(subscription().subscriptionId, principalId, sbdcRoleDefinition.id)
  properties: {
    principalType: 'ServicePrincipal'
    principalId: principalId
    roleDefinitionId: sbdcRoleDefinition.id
  }
}

//Grant Storage Blob Data Reader role to resource
resource grant_sbdr_role 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = if (grant_reader) {
  name: guid(subscription().subscriptionId, principalId, sbdrRoleDefinition.id)
  properties: {
    principalType: 'ServicePrincipal'
    principalId: principalId
    roleDefinitionId: sbdrRoleDefinition.id
  }
} 
