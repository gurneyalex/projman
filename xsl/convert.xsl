<?xml version="1.0" encoding="ISO-8859-1"?>

<xsl:stylesheet version="1.0" 
		xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    
  <xsl:output method="xml" encoding="iso-8859-1"></xsl:output>

  <xsl:template match="/"> 
    <xsl:apply-templates select="*"/>
  </xsl:template>

  <xsl:template match="*">
    <xsl:copy>
      <xsl:apply-templates select="@*"/>

      <xsl:apply-templates match="*|text()"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="@*">
    <xsl:attribute name="{name()}">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>

  <xsl:template match="projman">
    <project>
      <xsl:copy-of select="@*"/>

      <xsl:apply-templates select="*"/>
    </project>
  </xsl:template>

  <xsl:template match="import-project">
    <import-tasks>
      <xsl:copy-of select="@*"/>
    </import-tasks>
  </xsl:template>

  <xsl:template match="progress">
    <progress><xsl:value-of select=". div 100"/></progress>
  </xsl:template>


  <xsl:template match="@url">
    <xsl:attribute name="file">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>

  <xsl:template match="@usage">
    <xsl:attribute name="usage">
      <xsl:value-of select=". div 100"/>
    </xsl:attribute>
  </xsl:template>

</xsl:stylesheet>
