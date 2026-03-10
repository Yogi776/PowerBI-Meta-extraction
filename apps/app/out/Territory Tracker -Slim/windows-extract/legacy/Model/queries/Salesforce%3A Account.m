let
    Source = Salesforce.Data("https://login.salesforce.com/", [ApiVersion=60.0]),
    Account1 = Source{[Name="Account"]}[Data],
    #"Filtered Rows" = Table.SelectRows(Account1, each ([AccountNumber] <> null)),
    #"Removed Duplicates" = Table.Distinct(#"Filtered Rows", {"AccountNumber"}),
    #"Removed Other Columns" = Table.SelectColumns(#"Removed Duplicates",{"AccountNumber", "Name", "Sub_Key_Account__c", "Territory__c"}),
    #"Merged Queries" = Table.NestedJoin(#"Removed Other Columns", {"AccountNumber"}, #"SysPro-Salesforce Join", {"Salesforce Connector"}, "SysPro-Salesforce Join", JoinKind.LeftOuter),
    #"Expanded SysPro-Salesforce Join" = Table.ExpandTableColumn(#"Merged Queries", "SysPro-Salesforce Join", {"Customer"}, {"Customer"}),
    #"Replaced Value" = Table.ReplaceValue(#"Expanded SysPro-Salesforce Join",null,"Standard Account",Replacer.ReplaceValue,{"Sub_Key_Account__c"})
in
    #"Replaced Value"