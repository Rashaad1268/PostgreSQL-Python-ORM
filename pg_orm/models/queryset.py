class QuerySet(list):
    def __init__(self, model, query_set):
        self.model = model
        super().__init__(query_set)
    
    def append(self, model):
        if isinstance(model, self.model):
            super().append(model)
        else:
            raise TypeError

    def count(self):
        return len(self)

    def order_by(self, attribute):
        if hasattr(self.model, attribute):
            self.sort(key=lambda m: m.attribute)
        else:
            raise AttributeError(f"{self.model.__name__} has no attribute {attribute} to order by")

    @property
    def raw(self):
        return self

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self)

    def __eq__(self, other):
        return isinstance(other, QuerySet) and self.model == other.model and self.query_set == other.query_set
