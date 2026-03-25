
import lookForTesseract
import retriveSaveNPCsVoices
import getVoicesFromFile
import isQuestWindowOpen
import cleanText


# Create all required files and directories for the program
def create():

    # Setup Tesseract configuration
    lookForTesseract.create_tesseract_lang_file()
    lookForTesseract.create_tesseract_path_file()

    # Setup NPC voice storage
    retriveSaveNPCsVoices.create_npcs_voices_file()

    # Setup voice configuration paths
    getVoicesFromFile.create_voices_path_files()

    # Setup quest window detection assets
    isQuestWindowOpen.create_images_directory()

    # Setup text cleanup configuration
    cleanText.create_replace_string_file()