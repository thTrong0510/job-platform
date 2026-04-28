import cloudinary.uploader

class CloudinaryUtil:

    @staticmethod
    def upload_image(file):
        if not file:
            return None

        result = cloudinary.uploader.upload(
            file,
            folder="cv_avatars",
            resource_type="image"
        )

        return result.get("secure_url")