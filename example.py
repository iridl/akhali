from maproom import Maproom

mr = Maproom(
    title = "Example Maproom",
    prefix = "example",
)

mr.controls.group("First Group")
mr.controls.month(id="mon0")
mr.controls.text(id="txt0")
mr.controls.number(id="num0", min=0, max=100, default=50)

def hider(txt0):
    return txt0 != "hide"

mr.controls.group("Second Group", display=hider)
mr.controls.label("Hello, World!")

def output0(mon0, txt0):
    return mon0 + txt0

def output1(mon0, num0):
    return mon0 + str(num0)

mr.plots.group("First Tab")
mr.plots.output("First Output", output0)
mr.plots.output("Second Output", output1)

mr.plots.group("Second Tab")

if __name__ == "__main__":
    mr.start()
