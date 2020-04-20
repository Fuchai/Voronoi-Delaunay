class TryThis:
    def __init__(self):
        self.a=100

    @property
    def whatever(self):
        return self.a**10

if __name__ == '__main__':
    tt=TryThis()
    print(tt.whatever)