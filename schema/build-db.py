import subprocess
import util

config = util.get_config()["connection"]
user = config["user"]
database = config["database"]

# FIXME: This should be reading from the password in config rather than relying on PGPASSWORD env
# FIXME: Output is not very informative in terminal
process = subprocess.run(f'psql -f build-db.sql {database} {user}')
print(process.stdout)
