FROM python:3.14.7-slim
WORKDIR /app
COPY Inventory_manager.py .
CMD ["python", "Inventory_manager.py"]