class QuerySet:
    def __init__(self, model, query_set):
        self.model = model
        self.query_set = list(query_set)
    
    def append(self, model):
        if isinstance(model, self.model):
            self.query_set.append(model)
        else:
            raise TypeError

    def count(self):
        return len(self.query_set)

    def order_by(self, **kwargs):
        raise NotImplementedError()

    def __iter__(self):
        yield from self.query_set

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.query_set)

    def __eq__(self, other):
        return isinstance(other, QuerySet) and self.query_set == other.query_set

    def __len__(self):
        return len(self.query_set)

    def __getitem__(self, key):
        return self.query_set[key]

    def __delitem__(self, key):
        del self.query_set[key]
