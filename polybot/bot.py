import os
import time
import telebot
from PIL import Image
from loguru import logger
from telebot.types import InputFile
from img_proc import Img


class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError('Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')
        print(msg)

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ImageProcessingBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if self.is_current_msg_photo(msg):
            # Download the photo sent by the user
            img_path = self.download_user_photo(msg)
            # Process the image according to the caption provided
            self.process_image(msg['chat']['id'], img_path, msg.get('caption'))
        else:
            # Extract the user's first name
            first_name = msg['from'].get('first_name', 'there')
            # Greet the user by their name
            greeting_message = f"Hi, {first_name}! Please send a photo with a caption indicating the filter you wish to apply. Supported filters are: Blur, Contour, Segment, Rotate, Salt and Pepper, Concat, Median, Edge Extraction"
            self.send_text(msg['chat']['id'], greeting_message)

    def process_image(self, chat_id, img_path, caption):
        if caption:
            # Normalize the caption for comparison
            normalized_caption = caption.strip().lower()
            # Check the caption and apply the corresponding image processing filter
            if normalized_caption == 'blur':
                self.apply_custom_filter(chat_id, img_path, 'blur')
            elif normalized_caption == 'contour':
                self.apply_custom_filter(chat_id, img_path, 'contour')
            elif normalized_caption == 'concat':
                self.apply_concat_filter(chat_id, img_path)
            elif normalized_caption == 'segment':
                self.apply_custom_filter(chat_id, img_path, 'segment')
            elif normalized_caption.startswith('rotate'):
                try:
                    # Split the caption and extract the number of rotations
                    rotations = int(normalized_caption.split()[1])
                    self.apply_custom_filter(chat_id, img_path, 'rotate', rotations)
                except (IndexError, ValueError):
                    # If no number provided, default to 1 rotation
                    self.apply_custom_filter(chat_id, img_path, 'rotate', 1)
            elif normalized_caption.startswith('salt and pepper'):
                try:
                    # Split the caption and extract the number of iterations
                    iterations = int(normalized_caption.split()[3])
                    self.apply_custom_filter(chat_id, img_path, 'salt and pepper', iterations)
                except (IndexError, ValueError):
                    # If no number provided, default to 1 iteration
                    self.apply_custom_filter(chat_id, img_path, 'salt and pepper', 1)
            elif normalized_caption == 'median':
                self.apply_custom_filter(chat_id, img_path, 'median')
            elif normalized_caption == 'edge extraction':
                self.apply_custom_filter(chat_id, img_path, 'edge extraction')
            else:
                self.send_text(chat_id,
                               "Unsupported filter. Supported filters are: Blur, Contour, Segment, Rotate, Salt and Pepper, Concat, Median, Edge Extraction")
                self.send_text(chat_id,
                               "You can extend 'Rotate' and 'Salt and Pepper' filters by specify 'Rotate 2' to rotate the image twice, or 'Salt and Pepper 5' to make the image more noisy. Enjoy!")
        else:
            # If no caption provided, send a response indicating that a caption is required
            self.send_text(chat_id, "Please provide a filter caption with the photo.")

    def apply_custom_filter(self, chat_id, img_path, filter_name, rotations=1):
        # Instantiate the Img class with the provided image path
        img = Img(img_path)

        # Apply the specified filter
        if filter_name == 'blur':
            img.blur()
        elif filter_name == 'contour':
            img.contour()
        elif filter_name == 'segment':
            img.segment()
        elif filter_name == 'rotate':
            img.rotate(rotations)
        elif filter_name == 'salt and pepper':
            # Get the number of iterations from the `rotations` argument
            img.salt_n_pepper(iterations=rotations)
        elif filter_name == 'median':
            img.median()
        elif filter_name == 'edge extraction':
            img.edge_extraction()

        # Save the modified image
        new_img_path = img.save_img()

        # Send the modified image back to the user
        self.send_photo(chat_id, new_img_path)

        # Delete the temporary file
        os.remove(img_path)

    def apply_concat_filter(self, chat_id, img_path):
        # Apply concatenation filter to the image located at img_path
        original_img = Image.open(img_path)
        width, height = original_img.size
        half_width = width // 1
        processed_img = Image.new('RGB', (width * 2, height))
        processed_img.paste(original_img, (0, 0))
        processed_img.paste(original_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (half_width, 0))
        processed_img_path = f"{img_path.split('.')[0]}_concat.jpg"
        processed_img.save(processed_img_path)

        # Send the modified image back to the user
        self.send_photo(chat_id, processed_img_path)

        # Delete the temporary file
        os.remove(processed_img_path)
