import os
import logging
import shutil
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from app.domain.interfaces.ISeleniumManager import ISeleniumManager

class SeleniumManager(ISeleniumManager):
    logger = logging.getLogger(__name__)

    def __init__(self, download_dir: str = "/output/descargas", headless: bool = True, chrome_major: int = 141):
        self.download_dir = download_dir
        self.headless = headless
        self.chrome_major = chrome_major
        self.driver = None

    def init(self):
        """
        Inicializa el navegador Chrome con configuración personalizada y
        directorio de descargas automático.
        """
        try:
            os.makedirs(self.download_dir, exist_ok=True)

           # Opciones de Chrome
            chrome_opts = uc.ChromeOptions()
            chrome_opts.add_argument("--start-maximized")
            chrome_opts.add_argument("--no-sandbox")
            chrome_opts.add_argument("--disable-dev-shm-usage")
            chrome_opts.add_argument("--disable-popup-blocking")
            chrome_opts.add_argument("--disable-notifications")
            chrome_opts.add_argument("--window-size=1200,900")
           
            # Configuración para headless
            if self.headless:
                chrome_opts.add_argument("--headless=new")

            # 🧩 Preferencias de descarga
            prefs = {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "profile.default_content_settings.popups": 0,
            }
            chrome_opts.add_experimental_option("prefs", prefs)

            # User-Agent
            chrome_opts.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.chrome_major}.0.0.0 Safari/537.36"
            )

            # 🚀 Inicializar el driver
            self.driver = uc.Chrome(options=chrome_opts, version_main=self.chrome_major)

            # Ocultar bandera webdriver
            try:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception:
                pass

            self.logger.info("🟢 Driver de Selenium iniciado exitosamente.")
            return self.driver

        except Exception as e:
            raise RuntimeError(f"🔴 Error al iniciar Selenium: {e}")

    def get_driver(self):
        """
        Retorna el driver si está disponible.
        """
        if not self.driver:
            raise RuntimeError("El driver de Selenium no está inicializado o fue cerrado.")
        return self.driver

    def close(self):
        """
        Cierra el driver de forma segura, incluso si ya fue cerrado.
        """
        try:
            if self.driver:
                try:
                    self.driver.quit()
                    self.logger.info("🟢 Navegador Selenium cerrado correctamente.")
                except WebDriverException as e:
                    self.logger.warning(f"🟡 Error al cerrar con quit(): {e}, intentando cerrar servicio...")
                    try:
                        self.driver.service.stop()
                        self.logger.info("🟢 Servicio de Chrome detenido correctamente.")
                    except Exception as ex:
                        self.logger.warning(f"🟡 Error al detener servicio: {ex}")
            self.driver = None

        except Exception as e:
            self.logger.error(f"🔴 Error al cerrar Selenium: {e}")

