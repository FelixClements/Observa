#!/usr/bin/env bash
set -euo pipefail

codename="$(lsb_release -cs)"

sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -d /usr/share/postgresql-common/pgdg
sudo curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc -o /usr/share/postgresql-common/pgdg/pgdg.asc
echo "deb [signed-by=/usr/share/postgresql-common/pgdg/pgdg.asc] https://apt.postgresql.org/pub/repos/apt ${codename}-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
sudo apt update

sudo apt install -y postgresql-16 postgresql-client-16 postgresql-contrib

if [ -d /run/systemd/system ]; then
  sudo systemctl status postgresql --no-pager
else
  sudo service postgresql status || sudo service postgresql start
fi

sudo -u postgres psql -c "CREATE ROLE devuser WITH LOGIN PASSWORD 'devpass' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE devdb OWNER devuser;"

psql "postgresql://devuser:devpass@localhost:5432/devdb" -c "SELECT version();"
