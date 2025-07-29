# Use the official AWS Lambda Python runtime as a parent image
FROM public.ecr.aws/lambda/python:3.9

# Copy the requirements file into the container
COPY requirements.txt ./

# Install the specified packages
RUN pip install -r requirements.txt

# Copy the function code into the container
COPY main.py ./

# Set the CMD to your handler (could also be done in the Lambda console)
CMD [ "main.lambda_handler" ] 