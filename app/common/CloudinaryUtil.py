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

    def upload_cv_to_cloudinary(file_path):
        response = cloudinary.uploader.upload(
            file_path,
            resource_type="image",
            folder="cv_uploads",
            format="jpg",
            access_mode="public"
        )
        # Lưu 'secure_url' này vào MySQL
        return response.get("secure_url")