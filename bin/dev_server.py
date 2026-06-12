import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
import db as database
import models
from seed_dev_data import seed

app = create_app({
    "DATABASE": os.environ["DEV_DB"],
    "OPS_PASSWORD": os.environ["OPS_PASSWORD"],
})
with app.app_context():
    database.init_db()
    if not models.list_all_packers():
        seed()
        print("Seeded dev data: Maria (week 2) and Kai (just arrived).")
app.run(host="127.0.0.1", port=int(os.environ["PORT"]), debug=True)
