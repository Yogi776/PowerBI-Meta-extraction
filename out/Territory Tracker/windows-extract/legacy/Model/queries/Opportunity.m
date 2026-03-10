let
    Source = Salesforce.Data("https://login.salesforce.com/", [ApiVersion=48]),
    Opportunity1 = Source{[Name="Opportunity"]}[Data]
in
    Opportunity1