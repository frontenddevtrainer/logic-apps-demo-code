<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:ns0="http://schemas.microsoft.com/BizTalk/EDI/X12/2006"
  xmlns:csv="http://schemas.logicapps.demo/orders/csv"
  exclude-result-prefixes="csv">

  <xsl:output method="xml" indent="yes"/>

  <!-- Group rows by OrderNumber -->
  <xsl:key name="orders-by-number"
           match="csv:Orders/csv:Order"
           use="csv:OrderNumber"/>

  <xsl:template match="/">
    <ns0:X12_00401_850>

      <!-- One 850 per OrderNumber -->
      <xsl:for-each
        select="csv:Orders/csv:Order
                [generate-id()
                 = generate-id(key('orders-by-number', csv:OrderNumber)[1])]">

        <!-- ===== ST ===== -->
        <ns0:ST>
          <ns0:ST01>850</ns0:ST01>
          <ns0:ST02>
            <xsl:value-of select="format-number(position(), '0000')"/>
          </ns0:ST02>
        </ns0:ST>

        <!-- ===== BEG ===== -->
        <ns0:BEG>
          <ns0:BEG01>00</ns0:BEG01>
          <ns0:BEG02>NE</ns0:BEG02>
          <ns0:BEG03>
            <xsl:value-of select="csv:OrderNumber"/>
          </ns0:BEG03>
          <ns0:BEG05>
            <xsl:value-of select="csv:OrderDate"/>
          </ns0:BEG05>
        </ns0:BEG>

        <!-- ===== BUYER ===== -->
        <ns0:N1Loop>
          <ns0:N1>
            <ns0:N101>BY</ns0:N101>
            <ns0:N102><xsl:value-of select="csv:BuyerName"/></ns0:N102>
            <ns0:N103>ZZ</ns0:N103>
            <ns0:N104><xsl:value-of select="csv:BuyerId"/></ns0:N104>
          </ns0:N1>
        </ns0:N1Loop>

        <!-- ===== SELLER ===== -->
        <ns0:N1Loop>
          <ns0:N1>
            <ns0:N101>SE</ns0:N101>
            <ns0:N102><xsl:value-of select="csv:SellerName"/></ns0:N102>
            <ns0:N103>ZZ</ns0:N103>
            <ns0:N104><xsl:value-of select="csv:SellerId"/></ns0:N104>
          </ns0:N1>
        </ns0:N1Loop>

        <!-- ===== SHIP TO ===== -->
        <ns0:N1Loop>
          <ns0:N1>
            <ns0:N101>ST</ns0:N101>
            <ns0:N102><xsl:value-of select="csv:ShipToName"/></ns0:N102>
            <ns0:N103>ZZ</ns0:N103>
            <ns0:N104><xsl:value-of select="csv:ShipToId"/></ns0:N104>
          </ns0:N1>
          <ns0:N3>
            <ns0:N301><xsl:value-of select="csv:ShipToStreet"/></ns0:N301>
          </ns0:N3>
          <ns0:N4>
            <ns0:N401><xsl:value-of select="csv:ShipToCity"/></ns0:N401>
            <ns0:N402><xsl:value-of select="csv:ShipToState"/></ns0:N402>
            <ns0:N403><xsl:value-of select="csv:ShipToPostal"/></ns0:N403>
          </ns0:N4>
        </ns0:N1Loop>

        <!-- ===== PO1 LINE ITEMS ===== -->
        <xsl:for-each select="key('orders-by-number', csv:OrderNumber)">
          <ns0:PO1Loop>
            <ns0:PO1>
              <ns0:PO101><xsl:value-of select="csv:LineNumber"/></ns0:PO101>
              <ns0:PO102><xsl:value-of select="csv:Quantity"/></ns0:PO102>
              <ns0:PO103><xsl:value-of select="csv:UOM"/></ns0:PO103>
              <ns0:PO104><xsl:value-of select="csv:UnitPrice"/></ns0:PO104>
              <ns0:PO106>VP</ns0:PO106>
              <ns0:PO107><xsl:value-of select="csv:ItemSku"/></ns0:PO107>
            </ns0:PO1>
            <!-- PID - Product/Item Description (if available) -->
            <xsl:if test="csv:ItemDescription and csv:ItemDescription != ''">
              <ns0:PID>
                <ns0:PID01>F</ns0:PID01>
                <ns0:PID05><xsl:value-of select="csv:ItemDescription"/></ns0:PID05>
              </ns0:PID>
            </xsl:if>
          </ns0:PO1Loop>
        </xsl:for-each>

        <!-- ===== SE ===== -->
        <ns0:SE>
          <!-- Count segments: ST + BEG + 3×N1Loop + PO1Loop (PO1 + optional PID) + SE -->
          <ns0:SE01>
            <xsl:variable name="lineItems" select="key('orders-by-number', csv:OrderNumber)"/>
            <xsl:variable name="pidCount" select="count($lineItems[csv:ItemDescription and csv:ItemDescription != ''])"/>
            <!-- Base segments: ST(1) + BEG(1) + N1Loop(3) + SE(1) = 6 -->
            <!-- Plus: PO1 segments + PID segments -->
            <xsl:value-of select="6 + count($lineItems) + $pidCount"/>
          </ns0:SE01>
          <ns0:SE02>
            <xsl:value-of select="format-number(position(), '0000')"/>
          </ns0:SE02>
        </ns0:SE>

      </xsl:for-each>

    </ns0:X12_00401_850>
  </xsl:template>

</xsl:stylesheet>