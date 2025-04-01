// Parameters
@description('The name of the Fabric Capacity.')
param fabric_name string = 'fabricf2'

@description('The Azure Region to deploy the resources into.')
param location string = 'centralindia' // Central India

@description('The SKU name of the Fabric Capacity.')
@allowed([
  'F2'
  'F4'
  'F8'
  'F16'
  'F32'
  'F64'
  'F128'
  'F256'
  'F512'
  'F1024'
  'F2048'
])
param skuName string = 'F2'

@description('The SKU tier of the Fabric Capacity instance.')
param skuTier string = 'fabricf2'

@description('The list of administrators for the Fabric Capacity instance.')
@secure()
param adminUsers string = 'powerbipro@exponentia.ai'

// Variables
var suffix = uniqueString(resourceGroup().id)
var fabric_uniquename = '${fabric_name}${suffix}'

// Resource: Microsoft Fabric Capacity
resource fabricCapacity 'Microsoft.Fabric/capacities@2023-11-01' = {
  name: toLower(fabric_uniquename)
  location: location
  properties: {  
  sku: {
    name: skuName
    tier: skuTier
  }
  properties: {
    administration: {
      members: [adminUsers]
    }
  }
}

// Outputs
@description('The ID of the Fabric Capacity.')
output resourceId string = fabricCapacity.id

@description('The name of the Fabric Capacity.')
output resourceName string = fabricCapacity.name
