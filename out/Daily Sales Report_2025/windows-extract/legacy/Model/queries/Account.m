let
    Source = Salesforce.Data("https://login.salesforce.com/", [ApiVersion=48]),
    Account1 = Source{[Name="Account"]}[Data],
    #"Filtered Rows" = Table.SelectRows(Account1, each ([Active_Account__c] = "AC" or [Active_Account__c] = "On Hold"))
in
    #"Filtered Rows"