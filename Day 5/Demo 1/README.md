# Demo 1: Integration Account and X12 Schemas

This demo sets up the Integration Account artifacts that will be reused in later demos.

## Goal
- Create an Integration Account.
- Upload X12 850 schemas (and optionally a CSV flat file schema).
- Create partner identities and an agreement for X12 processing.

## Prerequisites
- An Azure subscription with permission to create Integration Accounts.
- Access to the standard X12 00401 schemas (use the Microsoft EDI schema package).
- All required schemas are located in `Day 5/schemas/` (shared across all demos).

## Cost-friendly notes
- Choose the **Integration Account Basic** tier; it is sufficient for schemas, maps, partners, and agreements.
- Delete the Integration Account after the demo to avoid ongoing charges.

## Steps
1. **Create the Integration Account**
   - Azure Portal -> Create resource -> Integration Account.
   - Choose the same region and resource group as your Logic App.

2. **Upload schemas**
   - Integration Account -> Schemas -> Add.
   - Upload `X12_00401_850.xsd` from `Day 5/schemas/`.
   - Optional: upload `orders-flatfile.xsd` from `Day 5/schemas/` (used in Demo 2-4).

3. **Create partners**
   - Integration Account -> Partners -> Add.
   - Add a **buyer** and **seller** partner with identifiers and qualifiers.
   - Suggested dummy values:
     - Partner 1 (Buyer)
       - Name: `ContosoRetail`
       - Identifier: `BUYER01`
       - Qualifier: `ZZ` (Mutually Defined)
       - Value: `BUYER01`
     - Partner 2 (Seller)
       - Name: `FabrikamSupplies`
       - Identifier: `SELLER01`
       - Qualifier: `ZZ` (Mutually Defined)
       - Value: `SELLER01`
   - If you select qualifier `1 - D-U-N-S`, the Value must be a 9-digit DUNS number (example: `123456789`).

4. **Create an agreement**
   - Integration Account -> Agreements -> Add.
   - Type: **X12** (not AS2).
   - Agreement form values:
     - Name: `ContosoRetail_To_FabrikamSupplies_X12`
     - Host Partner: `ContosoRetail`
     - Host Identity: `BUYER01` (Qualifier `ZZ`)
     - Guest Partner: `FabrikamSupplies`
     - Guest Identity: `SELLER01` (Qualifier `ZZ`)
   - Suggested dummy settings (good for demo/testing):
     - Interchange ID qualifier: `ZZ` (host and guest)
     - Interchange ID: `BUYER01` (host), `SELLER01` (guest)
     - Group ID: `PO` (Purchase Order)
     - Usage indicator: `T` (Test)
     - Delimiters: `*` (data element), `:` (component), `~` (segment)
     - Control numbers: start at `000000001`
     - Validation: enable envelope validation; keep strict segment validation optional for the demo

5. **Link the Integration Account to your Logic App**
   - Logic Apps Standard:
     - Open a workflow (create a simple HTTP or Recurrence workflow if needed).
     - Designer -> **Workflow settings** (gear icon) -> Integration account -> select the account.
     - If the Integration account option is missing, you are in the Standard experience that uses **Artifacts** instead of a linked Integration Account. In that case:
       - Logic App -> **Artifacts** -> add Schemas, Maps, Partners, and Agreements directly.
       - Skip linking the Integration Account and continue with Demo 3 using local artifacts.
   - Logic Apps Consumption:
     - Logic App -> Settings -> **Workflow settings** -> Integration account -> select the account.
   - If the account is not listed, confirm it is in the same subscription and region.

## What to point out live
- Schemas define message structure, maps define transformation logic.
- Partners and agreements control envelope settings, identifiers, and validation.
- The Integration Account is the shared repository for EDI artifacts used by Logic Apps.
