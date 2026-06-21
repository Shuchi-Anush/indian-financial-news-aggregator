# Infrastructure Preparation Guide

This directory is reserved for Terraform / Pulumi definitions for eventual cloud deployment.

## Intended Responsibilities
- Provisioning managed PostgreSQL (e.g., AWS RDS, GCP Cloud SQL).
- Provisioning container hosting (e.g., ECS, Cloud Run, GKE).

## Deployment Expectations
- The backend container is completely stateless (besides the DB). It can be scaled horizontally behind a Load Balancer.
- `DATABASE_URL` is the only strictly required secret.
- Advisory locks inside the application logic prevent the scheduler from overlapping if 5 identical backend containers are spun up concurrently.

## API Interaction Model
- The infrastructure layer must provision an internal network allowing the backend to reach the database, while exposing port 8000 to the public ingress controller.
