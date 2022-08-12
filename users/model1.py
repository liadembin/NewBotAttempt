from model import Model
import time
import schedule
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NiwidXNlcm5hbWUiOiJwbHBsIiwiaWF0IjoxNjYwMDI4MTE5fQ.SABgFBI6E1XAYrLiIg76vwaf5nk445sJeyGXwQ_FiT0"
model = Model("./KerasModels/Model1/model.h5", token,
              "./KerasModels/Model1/max.csv", idd="KerasModels/Model1")
print("Running")
while True:
    model.run_pending()
    time.sleep(1)
