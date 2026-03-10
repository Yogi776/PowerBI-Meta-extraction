let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("ZdDLCQMxDATQXnwWir62VEAaSI5L+m8j9gayMnsxDDzGko6j8YMfQmINGvcBnIREM+h6nq/nu33gaFKUBbAI+gJRkV5I0kFMf1W8KStVYqA+kHQFr8qLGh0iEyVnyIr6hXR+qEPReYa+VY1SxQQcc/ZxGyvK8MwgLqh2U3kpJ4cMxVxduimmUiYBIw0zzoU3Vm4vqqDBaEv0bUsux+/UIXOgy3nkP/t8AQ==", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [SorMaster.OrderDate = _t, NMscChargeValue = _t, MOrderQty = _t, MProductClass = _t]),
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"SorMaster.OrderDate", type datetime}, {"NMscChargeValue", type number}, {"MOrderQty", type number}})
in
    #"Changed Type"