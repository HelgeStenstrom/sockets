# import typing
# Behövs denna import? Inte om man kör PyCharm, ser det ut som.

# Typannoteringar som i catstr2 gör att man kan testa att argumenten ör av rätt typ.
# PyCharm kan detektera detta, även om typing inte importeras.

def catstr(a, b):
    return a + b + " actualluy"


def catstr2(a:str, b:str) -> str:
    return a + b + " actualluy"

def testCatstr():
    catstr(3, 4)
    catstr2("a", "b")
    catstr2(3, 4)
