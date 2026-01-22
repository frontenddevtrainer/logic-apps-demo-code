#!/usr/bin/env python3
"""
Setup script for Azurite development environment.
Creates required blob containers and uploads the default X12 850 mapping.
"""

from azure.storage.blob import BlobServiceClient

AZURITE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)

MAPPING_850 = """{
  "name": "X12 850 Purchase Order",
  "version": "1.0",
  "fields": {
    "purchaseOrderNumber": {"segment": "BEG", "element": 2},
    "purchaseOrderDate": {"segment": "BEG", "element": 4},
    "buyer.id": {"segment": "N1", "qualifier": {"element": 0, "value": "BY"}, "element": 3},
    "buyer.name": {"segment": "N1", "qualifier": {"element": 0, "value": "BY"}, "element": 1},
    "seller.id": {"segment": "N1", "qualifier": {"element": 0, "value": "SE"}, "element": 3},
    "seller.name": {"segment": "N1", "qualifier": {"element": 0, "value": "SE"}, "element": 1},
    "items[].productId": {"segment": "PO1", "element": 6},
    "items[].quantity": {"segment": "PO1", "element": 1},
    "items[].unitPrice": {"segment": "PO1", "element": 3},
    "items[].description": {"segment": "PID", "element": 4}
  }
}"""


def main():
    print("Connecting to Azurite...")
    service = BlobServiceClient.from_connection_string(AZURITE_CONNECTION_STRING)

    # Create containers
    containers = ["x12-mappings", "order-documents"]
    for container_name in containers:
        try:
            service.create_container(container_name)
            print(f"Created container: {container_name}")
        except Exception as e:
            if "ContainerAlreadyExists" in str(e):
                print(f"Container already exists: {container_name}")
            else:
                print(f"Error creating {container_name}: {e}")

    # Upload mapping file
    print("\nUploading X12 850 mapping...")
    blob_client = service.get_blob_client("x12-mappings", "mapping/standards/850.json")
    blob_client.upload_blob(MAPPING_850, overwrite=True)
    print("Uploaded: mapping/standards/850.json")

    # List all containers and blobs
    print("\nSetup complete! Current state:")
    for container in service.list_containers():
        print(f"\nContainer: {container.name}")
        container_client = service.get_container_client(container.name)
        for blob in container_client.list_blobs():
            print(f"  - {blob.name}")


if __name__ == "__main__":
    main()
