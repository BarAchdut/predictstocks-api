class HistoricalData:
    def __init__(self, date: str, price: float):
        self.date = date
        self.price = price

    def to_dict(self):
        return {"date": self.date, "price": self.price}
