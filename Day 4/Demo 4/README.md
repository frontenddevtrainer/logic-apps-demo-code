Day 4 Demo 4: Blob versioning + soft delete + lifecycle tiering

Goal
- Enable blob versioning and soft delete.
- Move deleted blob versions to a lower access tier during the soft delete window.
- Archive blobs in another container once they are older than 10 days.

Prereqs
- A general-purpose v2 storage account.
- Containers created (example: rawfiles, othercontainer).
- Owner/Contributor access to configure data protection and lifecycle policies.

Step 1: Enable versioning and soft delete (portal)
1. Storage account > Data protection.
2. Turn on "Enable versioning for blobs".
3. Turn on "Enable soft delete for blobs" and set a retention period (example: 7 days).
4. Optional: Turn on "Access tracking" if you later want lifecycle rules based on last access time.

Step 2: Configure lifecycle management policy
Notes
- Lifecycle rules run about once per day, not instantly.
- Archive tier is offline; reading requires rehydration.
- There is no filter "only when deleted". Use the "version" action set; deleted blobs leave versions behind.

Option A: Create the policy in the portal
1. Storage account > Data management > Lifecycle management > Add a rule.
2. Rule 1 (versions to lower tier):
   - Scope: Limit to container rawfiles (prefix rawfiles/).
   - Blob types: Block blobs.
   - Base blobs: No action.
   - Blob versions: Move to cool after 0-1 days, move to archive after 10 days, delete after 30 days (optional).
3. Rule 2 (archive old blobs in other container):
   - Scope: Limit to container othercontainer (prefix othercontainer/).
   - Blob types: Block blobs.
   - Base blobs: Move to archive after 10 days since last modification.

Option B: Apply a JSON policy (CLI/ARM)
Save as lifecycle.json, then apply in the portal or with:
az storage account management-policy create --account-name <account> --resource-group <rg> --policy @lifecycle.json

Example lifecycle.json
{
  "rules": [
    {
      "enabled": true,
      "name": "tier-versions-after-delete",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["rawfiles/"]
        },
        "actions": {
          "version": {
            "tierToCool": { "daysAfterCreationGreaterThan": 0 },
            "tierToArchive": { "daysAfterCreationGreaterThan": 10 },
            "delete": { "daysAfterCreationGreaterThan": 30 }
          }
        }
      }
    },
    {
      "enabled": true,
      "name": "archive-other-container-after-10-days",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["othercontainer/"]
        },
        "actions": {
          "baseBlob": {
            "tierToArchive": { "daysAfterModificationGreaterThan": 10 }
          }
        }
      }
    }
  ]
}

Step 3: Validate
1. Upload a blob into rawfiles, update it once to create a version, then delete it.
2. Check versions in the Azure Portal (Blob > Versions) and confirm the tier changes after policy runs.
3. Upload a blob to othercontainer and wait for it to be archived after 10 days.