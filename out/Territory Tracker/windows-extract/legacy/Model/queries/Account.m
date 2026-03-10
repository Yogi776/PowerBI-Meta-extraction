let
    Source = Salesforce.Data("https://login.salesforce.com/", [ApiVersion=60.0]),
    Account1 = Source{[Name="Account"]}[Data],
    #"Filtered Rows" = Table.SelectRows(Account1, each ([AccountNumber] <> null) and ([Active_Account__c] = "Active")),
    #"Removed Duplicates" = Table.Distinct(#"Filtered Rows", {"AccountNumber"})
in
    #"Removed Duplicates"