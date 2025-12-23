# Demo 2: Build an XSLT Map (CSV -> X12 850)

This demo uses Visual Studio and the Enterprise Integration Tools to create a map that transforms CSV order data into an X12 850 structure.

## Goal
- Create a flat file schema for CSV input.
- Reference the X12 850 schema.
- Build and export an XSLT map for the Integration Account.

## Prerequisites
- Visual Studio 2019 or 2022.
- Azure Logic Apps Enterprise Integration Tools extension installed.
- X12 00401 schemas from `Day 5/schemas/X12_00401_850.xsd`.
- Sample data: `Day 5/Demo 2/sample-data/orders.csv`.
- Reference schema: `Day 5/schemas/orders-flatfile.xsd` (if you want to skip the wizard).
- Demo 1 partner/agreement values (for consistency):
  - Buyer: `ContosoRetail` / `BUYER01` / qualifier `ZZ`
  - Seller: `FabrikamSupplies` / `SELLER01` / qualifier `ZZ`
  - Agreement: `ContosoRetail_To_FabrikamSupplies_X12` (Type `X12`)

## Steps
1. **Create an Integration Account project**
   - File -> New -> Project -> Integration Account (Logic Apps).

2. **Add the flat file schema**
   - Add -> New Item -> Flat File Schema Wizard.
   - Delimited file, first row contains headers.
   - Use the column set in `Day 5/Demo 2/sample-data/orders.csv`.
   - Alternatively, import `Day 5/schemas/orders-flatfile.xsd`.

3. **Add the X12 850 schema**
   - Add -> Existing Item -> Import `Day 5/schemas/X12_00401_850.xsd`.
   - Also add any referenced X12 schema dependencies.

4. **Create the map**
   - Add -> New Item -> Map.
   - Source: the CSV flat file schema.
   - Destination: the X12 850 schema.
   - Create links using the mapping table below.

5. **Test the map**
   - Right-click the map -> Test Map.
   - Use the sample CSV converted to XML (or the XML output of the flat file decoder).

6. **Export the XSLT**
   - Right-click the map -> Validate Map.
   - The generated `.xslt` is produced in the output folder.
   - Upload the XSLT to the Integration Account -> Maps.

## Mapping checklist (example)
| CSV field | X12 segment/element |
| --- | --- |
| OrderNumber | BEG03 (Purchase Order Number) |
| OrderDate | BEG05 (Date, CCYYMMDD) |
| BuyerName | N1 (BY) N102 |
| BuyerId | N1 (BY) N104 |
| SellerName | N1 (SE) N102 |
| SellerId | N1 (SE) N104 |
| ShipToName | N1 (ST) N102 |
| ShipToId | N1 (ST) N104 |
| ShipToStreet | N3 (ST) N301 |
| ShipToCity | N4 (ST) N401 |
| ShipToState | N4 (ST) N402 |
| ShipToPostal | N4 (ST) N403 |
| LineNumber | PO101 |
| Quantity | PO102 |
| UOM | PO103 |
| UnitPrice | PO104 |
| ItemSku | PO106 (Qualifier VP) |
| ItemDescription | PO108 (Qualifier PD) |

## What to point out live
- Flat file schemas turn CSV into XML, which is the input for XSLT.
- X12 schemas represent the EDI XML structure, not the raw EDI text.
- The map exports to XSLT, which is what Logic Apps uses in the Integration Account.

## Cost-friendly notes
- Map creation and testing happen locally in Visual Studio; no Azure cost until you upload the XSLT.
