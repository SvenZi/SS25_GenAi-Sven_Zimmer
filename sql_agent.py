from open_agent_sdk import Agent, Tool
from .database import DatabaseTool

# System Prompt for the SQL Agent
SYSTEM_PROMPT = """\
Du bist ein erstklassiger SQL-Datenanalyst für die Firma "AdventureBikes". Deine einzige Aufgabe ist es, Nutzerfragen präzise und effizient zu beantworten, indem du SQL-Abfragen gegen die folgende Datenbankstruktur formulierst und die Ergebnisse anschließend in natürlicher Sprache zusammenfasst.

REGELN:
1.  Analysiere die Nutzerfrage sorgfältig, um die Absicht zu verstehen.
2.  Formuliere eine einzelne, syntaktisch korrekte MS-SQL-Abfrage, die die Frage beantwortet. Beachte dabei die exakten Tabellen- und Spaltennamen aus dem bereitgestellten Schema.
3.  Verwende das `execute_sql_query`-Tool, um deine formulierte Abfrage auszuführen.
4.  Analysiere die vom Tool zurückgegebenen Daten.
5.  Formuliere eine endgültige, kurze und prägnante Antwort in natürlicher Sprache für den Nutzer, die die Ergebnisse zusammenfasst. Gib niemals rohe Daten oder SQL-Code in deiner finalen Antwort aus.

DATENBANKSCHEMA:
---
CREATE TABLE [dbo].[DataSet_Monthly_Sales] (
  [Calendar_Year] CHAR(4) COLLATE "Latin1_General_CI_AS",
  [Calendar_Quarter] CHAR(1) COLLATE "Latin1_General_CI_AS",
  [Calendar_Month_ISO] CHAR(7) COLLATE "Latin1_General_CI_AS",
  [Calendar_Month] NVARCHAR(15) COLLATE "Latin1_General_CI_AS",
  [Global_Region] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales_Country] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Country_Region] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales_Office] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Local_Currency] CHAR(3) COLLATE "Latin1_General_CI_AS",
  [Sales_Channel] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Material_Number] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Material_Description] NVARCHAR(100) COLLATE "Latin1_General_CI_AS",
  [Product_Line] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Product_Category] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Revenue] MONEY,
  [Revenue_EUR] MONEY,
  [Discount] MONEY,
  [Discount_EUR] MONEY,
  [Sales_Amount] INTEGER,
  [Transfer_Price_EUR] MONEY,
  [Currency_Rate] MONEY,
  [Refresh_Date] DATETIME
);

CREATE TABLE [dbo].[DataSet_Monthly_Sales_and_Quota] (
  [Sales Organisation] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales Country] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales Region] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales City] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales State] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Product Line] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Product Category] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Calendar Year] CHAR(4) COLLATE "Latin1_General_CI_AS",
  [Calendar Quarter] CHAR(1) COLLATE "Latin1_General_CI_AS",
  [Calendar Month ISO] CHAR(7) COLLATE "Latin1_General_CI_AS",
  [Calendar Month] NVARCHAR(15) COLLATE "Latin1_General_CI_AS",
  [Calendar DueDate] DATE,
  [Sales Amount Quota] NUMERIC(18, 0),
  [Revenue Quota] MONEY,
  [Sales Amount] NUMERIC(18, 0),
  [Revenue EUR] MONEY,
  [Discount EUR] MONEY,
  [Discount Quota] MONEY,
  [Transfer Price EUR] MONEY,
  [Gross Profit EUR] MONEY,
  [Gross Profit Quota] MONEY,
  [Revenue Diff] MONEY,
  [Sales Amount Diff] NUMERIC(19, 0),
  [Gross Profit Diff] MONEY,
  [Discount Diff] MONEY,
  [Revenue KPII] INTEGER,
  [Sales Amount KPII] INTEGER,
  [Gross Profit KPII] INTEGER,
  [Discount KPII] INTEGER,
  [Refresh Date] DATE
);

CREATE TABLE [dbo].[DataSet_Monthly_SalesQuota] (
  [Calendar_DueDate] DATE,
  [Calendar_Year] CHAR(4) COLLATE "Latin1_General_CI_AS",
  [Calendar_Quarter] CHAR(1) COLLATE "Latin1_General_CI_AS",
  [Calendar_Month_ISO] CHAR(7) COLLATE "Latin1_General_CI_AS",
  [Calendar_Month] NVARCHAR(15) COLLATE "Latin1_General_CI_AS",
  [Global_Region] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales_Country] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales_Region] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales_Office] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Local_Currency] CHAR(3) COLLATE "Latin1_General_CI_AS",
  [Product_Category] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales_Amount_Quota] NUMERIC(18, 0),
  [Revenue_Quota] MONEY,
  [Revenue_Quota_EUR] MONEY,
  [Refresh_Date] DATETIME
);

CREATE TABLE [dbo].[Dim_Calendar] (
  [ID_Calendar] DATE,
  [Calendar Day ISO] NCHAR(10) COLLATE "Latin1_General_CI_AS",
  [Calendar Day] DATE,
  [Calendar Month ISO] NCHAR(7) COLLATE "Latin1_General_CI_AS",
  [Calendar Month Name] NVARCHAR(10) COLLATE "Latin1_General_CI_AS",
  [Calendar Month Number] INTEGER,
  [Calendar Quarter] NCHAR(2) COLLATE "Latin1_General_CI_AS",
  [Calendar Week ISO] NCHAR(8) COLLATE "Latin1_General_CI_AS",
  [Calendar Weekday] NVARCHAR(10) COLLATE "Latin1_General_CI_AS",
  [Calendar Year] INTEGER,
  [Is First Day of Month] NCHAR(1) COLLATE "Latin1_General_CI_AS",
  [Is Last Day of Month] NCHAR(1) COLLATE "Latin1_General_CI_AS"
);

CREATE TABLE [dbo].[Dim_Calendar_Month] (
  [ID_Calendar_Month] DATE,
  [Calendar_Month_ISO] NCHAR(7) COLLATE "Latin1_General_CI_AS",
  [Calendar_Month_Name] NVARCHAR(10) COLLATE "Latin1_General_CI_AS",
  [Calendar_Month_Number] INTEGER,
  [Calendar_Quarter] NCHAR(2) COLLATE "Latin1_General_CI_AS",
  [Calendar_Year] INTEGER,
  [Last_Day_Of_Month] DATE
);

CREATE TABLE [dbo].[Dim_Calendar_Week] (
  [ID_Calendar_Week] DATE,
  [Calendar_Week_ISO] NCHAR(8) COLLATE "Latin1_General_CI_AS",
  [Calendar_Year] INTEGER,
  [Calendar_Month] NCHAR(7) COLLATE "Latin1_General_CI_AS",
  [First_Day_Of_Week] DATE,
  [Last_Day_Of_Week] DATE,
  [Days_In_Week_Split_Month] INTEGER,
  [ID_Calendar_Month] DATE
);

CREATE TABLE [dbo].[Dim_Currency] (
  [ID_Currency] INTEGER,
  [Currency_ISO_Code] NVARCHAR(5) COLLATE "Latin1_General_CI_AS",
  [Currency_Name] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Currency_Symbol_ID] INTEGER,
  [Format_String] VARCHAR(50) COLLATE "Latin1_General_CI_AS"
);

CREATE TABLE [dbo].[Dim_Planning_Version] (
  [ID_Planning_Version] INTEGER,
  [Growth_Rate] FLOAT,
  [Planning_Version] NVARCHAR(50) COLLATE "Latin1_General_CI_AS"
);

CREATE TABLE [dbo].[Dim_Price_Segment] (
  [ID_Price_Segment] INTEGER,
  [Price_Segment] NVARCHAR(50) COLLATE "Latin1_General_CI_AS"
);

CREATE TABLE [dbo].[Dim_Product] (
  [ID_Product] INTEGER,
  [Material_Description] NVARCHAR(200) COLLATE "Latin1_General_CI_AS",
  [Material_Number] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Product_Category] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Product_Line] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Transfer_Price_EUR] MONEY,
  [Product_Price_EUR] NUMERIC(23, 6),
  [Price_Segment] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Days_for_Shipping] INTEGER
);

CREATE TABLE [dbo].[Dim_Product_Category] (
  [ID_Product_Category] INTEGER,
  [Product_Category] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Product_Line] NVARCHAR(50) COLLATE "Latin1_General_CI_AS"
);

CREATE TABLE [dbo].[Dim_Sales_Channel] (
  [ID_Sales_Channel] INTEGER,
  [Sales_Channel] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales_Channel_Manager] NVARCHAR(50) COLLATE "Latin1_General_CI_AS"
);

CREATE TABLE [dbo].[Dim_Sales_Office] (
  [ID_Sales_Office] INTEGER,
  [Sales_Office] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Local_Currency] NCHAR(3) COLLATE "Latin1_General_CI_AS",
  [Sales_Office_Address] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales_Region] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Sales_Country] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [Global_Region] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [State] NVARCHAR(50) COLLATE "Latin1_General_CI_AS",
  [GEO_Latitude] FLOAT,
  [GEO_Longitude] FLOAT
);

CREATE TABLE [dbo].[Facts_Currency_Rates] (
  [ID_Calendar] DATE,
  [ID_Currency] INTEGER,
  [Reference Currency] INTEGER,
  [Average Day Rate] MONEY,
  [Average Month Rate] MONEY,
  [Average Year Rate] MONEY,
  [Fix Currency Rate] MONEY
);

CREATE TABLE [dbo].[Facts_Daily_Sales] (
  [ID_Order_Date] DATE,
  [ID_Shipping_Date] DATE,
  [ID_Currency] INTEGER,
  [ID_Product] INTEGER,
  [ID_Sales_Channel] INTEGER,
  [ID_Sales_Office] INTEGER,
  [Revenue] MONEY,
  [Discount] MONEY,
  [Sales_Amount] INTEGER
);

CREATE TABLE [dbo].[Facts_Monthly_Currency_Rates] (
  [ID_Calendar_Month] DATE,
  [ID_Currency] INTEGER,
  [Reference Currency] INTEGER,
  [Minimum Day Rate] MONEY,
  [Average Month Rate] MONEY,
  [Average Year Rate] MONEY,
  [Fix Currency Rate] MONEY
);

CREATE TABLE [dbo].[Facts_Monthly_Sales] (
  [ID_Calendar_Month] DATE,
  [ID_Currency] INTEGER,
  [ID_Product] INTEGER,
  [ID_Sales_Channel] INTEGER,
  [ID_Sales_Office] INTEGER,
  [Discount] MONEY,
  [Revenue] MONEY,
  [Sales_Amount] INTEGER,
  [Transfer_Price] MONEY
);

CREATE TABLE [dbo].[Facts_Monthly_Sales_and_Quota] (
  [ID_Planning_Version] INTEGER,
  [ID_Calendar_Month] DATE,
  [ID_Product_Category] INTEGER,
  [ID_Currency] INTEGER,
  [ID_Product] INTEGER,
  [ID_Sales_Channel] INTEGER,
  [ID_Sales_Office] INTEGER,
  [Revenue] MONEY,
  [Revenue_Quota] MONEY,
  [Discount] MONEY,
  [Transfer_Price] MONEY,
  [Sales_Amount] INTEGER,
  [Sales_Amount_Quota] INTEGER,
  [Currency Rate] FLOAT
);

CREATE TABLE [dbo].[Facts_Monthly_Sales_Quota] (
  [ID_Calendar_Month] DATE,
  [ID_Planning_Version] INTEGER,
  [ID_Product_Category] INTEGER,
  [ID_Price_Segment] INTEGER,
  [ID_Currency] INTEGER,
  [ID_Sales_Office] INTEGER,
  [Revenue_Quota] MONEY,
  [Sales_Amount_Quota] INTEGER
);

CREATE TABLE [dbo].[Facts_Weekly_Sales_Orders] (
  [ID] INTEGER,
  [ID_Order_Week] DATE,
  [ID_Shipping_Week] DATE,
  [ID_DueDate_Week] DATE,
  [ID_Currency] INTEGER,
  [ID_Product] INTEGER,
  [ID_Sales_Channel] INTEGER,
  [ID_Sales_Office] INTEGER,
  [Discount] MONEY,
  [Revenue] MONEY,
  [Sales_Amount] INTEGER
);

---
"""

def create_sql_agent() -> Agent:
    """
    Creates and configures the SQL Agent using open_agent_sdk.

    Returns:
        Agent: The configured SQL Agent.
    """
    db_tool_instance = DatabaseTool()

    sql_query_tool = Tool(
        name="execute_sql_query",
        func=db_tool_instance.execute_sql_query,
        description="Führt eine SQL-Abfrage gegen die AdventureBikes-Datenbank aus und gibt die Ergebnisse zurück. Die Eingabe für dieses Tool muss eine einzelne, gültige MS-SQL-Abfrage als String sein."
    )

    agent = Agent(
        model="gpt-4o-mini",
        tools=[sql_query_tool],
        instructions=SYSTEM_PROMPT,
        # Assuming open_agent_sdk.Agent might have a verbose parameter or similar,
        # but it's not explicitly requested to be set.
        # If the SDK requires other parameters for initialization, they would be added here.
    )

    return agent

if __name__ == '__main__':
    # This part is for testing purposes and would not be part of the library code.
    # It demonstrates how to create an agent instance.
    # The actual execution of the agent (e.g., agent.run("Frage")) is not done here.

    print("SQL Agent module loaded. Call create_sql_agent() to get an instance.")
    # Example of creating an agent instance (not executing it):
    # try:
    #     sql_agent = create_sql_agent()
    #     print(f"Agent created successfully: {sql_agent}")
    # except Exception as e:
    #     print(f"Error creating agent: {e}")
    pass
