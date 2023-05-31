from maproom import Maproom
import xarray as xr
from pingrid import CMAPS

mr = Maproom(
    title = "Example Maproom",
    prefix = "example",
)

mr.marker(id="mark", position=[-29.3151, 27.4869])

if __name__ == "__main__":
    mr.start()
