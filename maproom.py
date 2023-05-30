from akhali import Maproom

mr = Maproom(
    title = "Monthly Climatology",
    prefix = "monthly",
)

# - finish number
# - finish output
# _ margins
# add test data
# hiding system
# put on github
# adjust names
# convert to example
# no main?

mr.controls.group("First Group")
mr.controls.month(id="m0")
mr.controls.label("foo")
mr.controls.month(id="m1")
mr.controls.text(id="t1")

mr.controls.group("Second Group")
mr.controls.select(id="s0", options=["ABC", "XYZ"], default="XYZ")
mr.controls.number(id="num0", min=0, max=100, default=50)

def hider(num0):
    return num0 >= 50

mr.controls.group("Third Group", display=hider)
mr.controls.label("Hello, World!")

def nothing(s0, m0, m1):
    return s0 + m0 + m1

def nothing2(m0, m1):
    return m0 + m1

mr.plots.group("First Tab")
mr.plots.output("Out1", nothing)
mr.plots.output("Out2", nothing2)

mr.plots.group("Second Tab")

if __name__ == "__main__":
    mr.start()
