#!/bin/bash

set -e
trap 'echo "❌ Backup failed!"' ERR

if [ -f .env ]; then
  source .env
else
  echo ".env file not found!"
  exit 1
fi

TIMESTAMP=$(date +%F-%H-%M-%S)

BACKUP_DIR=/backups

mkdir -p $BACKUP_DIR

# Run pg_dump inside the Docker container
docker exec -i $CONTAINER_NAME pg_dump -U $DB_USER  $DB_NAME > $BACKUP_DIR/db-backup-$TIMESTAMP.sql

# Compress the backup
gzip $BACKUP_DIR/db-backup-$TIMESTAMP.sql

gpg --batch --yes --symmetric --cipher-algo AES256 --passphrase $GPG_PASSPHRASE -o $BACKUP_DIR/db-backup-$TIMESTAMP.sql.gz.gpg $BACKUP_DIR/db->

# Upload the backup to S3
aws s3 cp $BACKUP_DIR/db-backup-$TIMESTAMP.sql.gz.gpg s3://$S3_BUCKET_NAME/ --sse AES256

echo "✅ Backup completed and securely uploaded to S3!"