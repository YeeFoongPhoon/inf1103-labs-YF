FROM python:3.14.7-slim
WORKDIR /app
COPY Inventory_manager_updated.py .
CMD ["python", "Inventory_manager_updated.py"]