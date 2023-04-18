# TODO(Project 1): Implement Backend according to the requirements.
from google.cloud import storage
from google.cloud import exceptions
from flask_login import current_user
import hashlib
import io
from flask import Flask


class Backend:

    def __init__(self, storage_client=storage.Client()):
        self.storage_client = storage_client

    def get_wiki_page(self, name):
        """Gets the contents of the specified wiki page.

        Args:
            name: The name of the wiki page.

        Returns:
            The contents of the wiki page.

        Raises:
            Exception: If there is a network error.
        """
        bucket = self.storage_client.bucket("sdswiki_contents")
        blob = bucket.get_blob(name)
        if blob is None:
            return f"Error: Wiki page {name} not found."

        try:
            with blob.open() as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Network error: {e}"

    def get_all_page_names(self):
        """Gets the names of all wiki pages.

        Returns:
            A list of the names of all wiki pages.

        Raises:
            Exception: If there is a network error.
        """
        try:
            pages_names_list = []
            blobs = self.storage_client.list_blobs("sdswiki_contents")

            if not blobs:
                return "Error: No pages found in bucket."

            for blob in blobs:
                pages_names_list.append(blob.name)

            return pages_names_list

        except Exception as e:
            return f"Network error: {e}"

    def upload(self, data, destination_blob_name, username, override=False):
        '''
        Uploads page to Wiki server

        Args:
            destination_blob_name = name of page to be uploaded
            data = the information to be displayed on the page

        returns:
            A response message stating if your upload was successful or not.
            If the upload was unsuccessulf, the reason why would be displayed.
        '''

        if data == b'' or data == '':
            if override:
                return 'You cannot delete all the contents of a pge. Please delete the page instead.'
            return 'Please upload a file.'

        if destination_blob_name == '':
            return 'Please provide the name of the page.'

        blobs = self.storage_client.list_blobs('sdswiki_contents')
        bucket = self.storage_client.bucket('sdswiki_contents')

        for blob in blobs:
            if destination_blob_name == blob.name and override == False:
                return 'Upload failed. You cannot overrite an existing page'

        blob = bucket.blob(destination_blob_name)

        # Set the x-goog-meta-author metadata header
        blob.metadata = {'author': username}

        blob.upload_from_string(data)

        if override:
            return f"The page titled {destination_blob_name} was successfully updated."
        return f"{destination_blob_name} uploaded to Wiki."

    def report(self, page, message):
        '''
        Saves the report message for a page in backend
        Args: The page being reported, and the message of the report
        Returns: A message stating the status of the report made.
        '''
        if message == '':
            return 'You need to enter a message'
        bucket = self.storage_client.bucket('sds_reports')

        blob = bucket.get_blob(page)
        if blob == None:
            blob = bucket.blob(page)

        blob.upload_from_string(message)
        return "Your report was sent successfully."

    def sign_up(self, name, password):
        '''
        Allows a person to create an account on the wiki if they are using it for the first time.

        Args:
            name = This acts as the username of the person
            password = The password associated with the account for the wiki

        Returns:
            A message letting you know if your account was successfully created,
            or if it was unsuccessful because the user already exists.
        '''
        bucket = self.storage_client.bucket('sdsusers_passwords')
        blobs = self.storage_client.list_blobs('sdsusers_passwords')

        for blob in blobs:
            if blob.name == name:
                return f"user {name} already exists in the database. Please sign in."

        blob = bucket.blob(name)
        with blob.open("w") as user:
            salty_password = f"{name}{password}".encode()
            secure_password = hashlib.sha3_256(salty_password).hexdigest()
            user.write(secure_password)

        return f"user {name} successfully created."

    #Checks the buckets to ensure correct info is being used for logins
    def sign_in(self, username, password):
        '''
        Allows a person to sign into their wiki account.

        Args:
            name = This acts as the username of the person
            password = The password associated with the account for the wiki

        Returns:
            A message letting you know if login was successful or not.
        '''
        salty_password = f"{username}{password}".encode()
        hashed = hashlib.sha3_256(salty_password).hexdigest()
        blobs = self.storage_client.list_blobs('sdsusers_passwords')
        stored = False

        for blob in blobs:
            if username == blob.name:
                with blob.open("r") as username:
                    secure_password = username.read()
                stored = True
        if not stored:
            return "Username not found"

        if hashed == secure_password:
            return 'Sign In Successful'
        return 'Incorrect Password'

    def get_image(self, name):
        '''
        Allows images to be pulled from the bucket and sent to the html pages. 

        Args:
            name = This name of the picture

        Returns:
            Binary form of the image reqested.
        '''
        bucket = self.storage_client.bucket('sdsimages')
        blob = bucket.blob(name)

        with blob.open("rb") as f:
            img = f.read()

        return img

    def check_page_author(self, page_name):
        """
        Retrieves the author metadata of a blob with the given name from the Google Cloud Storage bucket.

        Args:
            name (str): The name of the blob to retrieve the author metadata from.

        Returns:
        If the specified blob exists and has an author metadata, returns the author's name as a string.
        If the specified blob does not exist or does not have an author metadata, returns None.
        If an error occurs while retrieving the metadata, returns None and prints an error message.
        """

        bucket = self.storage_client.bucket("sdswiki_contents")
        blob = bucket.get_blob(page_name)
        if blob:
            try:
                metadata = blob.metadata
                author = metadata.get('author')
                if author:
                    return author
                else:
                    return 'Unknown'

            except AttributeError:
                return 'Unknown'

        else:
            return 'Unknown'

    def delete_page(self, name):
        '''
        Delete a page from the back end
        Args: Page name
        Return: True if page is deleted
        '''
        blobs = self.storage_client.list_blobs('sdswiki_contents')
        for blob in blobs:
            if blob.name == name:
                blob.delete()
                return True
        return False
