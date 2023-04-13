from akhali import Maproom

monthly = Maproom(
    title = "Monthly Climatology",
    prefix = "monthly",
)

monthly.tab(id="tab1", label="First Tab")
monthly.tab(id="tab2", label="Second Tab")
monthly.tab(id="tab3", label="Third Tab")

monthly.block(id="block1", label="First Block")
monthly.block(id="block2", label="Second Block")

monthly.text("This is some text", block="block1")
monthly.text("...and so is this", block="block2")

monthly.month(id="mon0", block="block2")
monthly.month(id="mon1", label="Separate Month")


monthly.text("...This is more text", block="block2")

monthly.select(id="sel0", options=["ABC", "XYZ"],
               default="XYZ", block="block2")

monthly.data(id="enacts", path="./zarr")

def climatology(data, inputs):
    return None

monthly.layer(label="Monthly Climatology",
              data="enacts",
              inputs=["mon1", "mon1"],
              function=climatology)


if __name__ == "__main__":
    monthly.start()
