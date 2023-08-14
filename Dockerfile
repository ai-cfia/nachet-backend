# Use the Python 3 image
FROM python:3

# Set the working directory inside the container
WORKDIR /app

# Set environment variables for your Quart app
ENV QUART_APP=app.py
ENV QUART_ENV=development

# Copy just the requirements file first, to leverage Docker cache
COPY ./requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Now, copy the rest of your application to the container
COPY . .

# Run the application using Hypercorn
CMD ["hypercorn", "app:app", "--reload"]
