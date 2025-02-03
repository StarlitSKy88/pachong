import aiohttp
import asyncio
import re
from typing import List, Optional
from abc import ABC, abstractmethod
from loguru import logger
from bs4 import BeautifulSoup
import random
import time

class BaseProxyProvider(ABC):
    """代理提供者基类"""
    
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.logger = logger.bind(name=f"proxy_provider_{name}")
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 5
    
    @abstractmethod
    async def get_proxies(self) -> List[str]:
        """获取代理列表"""
        pass

    async def parse(self, content: str) -> List[str]:
        """解析代理列表"""
        raise NotImplementedError()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.logger.debug(f"Closed session for {self.name}")

    async def get_proxies(self) -> List[str]:
        """获取代理列表"""
        self.logger.info(f"Fetching proxies from {self.name} ({self.url})")
        
        for retry in range(self.max_retries):
            try:
                if not self.session:
                    self.session = aiohttp.ClientSession(headers=self.headers)
                    self.logger.debug(f"Created new session for {self.name}")
                    
                async with self.session.get(
                    self.url,
                    timeout=self.timeout,
                    allow_redirects=True
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        content_length = len(content)
                        self.logger.debug(f"Got response from {self.name}: {content_length} bytes")
                        
                        if content_length > 0:
                            proxies = await self.parse(content)
                            valid_proxies = [p for p in proxies if self._validate_proxy(p)]
                            
                            self.logger.info(
                                f"Got {len(valid_proxies)} valid proxies from {self.name} "
                                f"(total: {len(proxies)}, invalid: {len(proxies) - len(valid_proxies)})"
                            )
                            return valid_proxies
                        else:
                            self.logger.warning(f"Empty response from {self.name}")
                    else:
                        self.logger.warning(
                            f"Failed to fetch from {self.name}: "
                            f"status {response.status} ({response.reason})"
                        )
                        
            except aiohttp.ClientError as e:
                self.logger.error(f"Network error from {self.name}: {e}")
            except asyncio.TimeoutError:
                self.logger.error(f"Timeout error from {self.name} after {self.timeout}s")
            except Exception as e:
                self.logger.error(f"Error fetching from {self.name}: {e}")
                
            if retry < self.max_retries - 1:
                self.logger.info(f"Retrying {self.name} in {self.retry_delay}s (attempt {retry + 2}/{self.max_retries})")
                await asyncio.sleep(self.retry_delay)
                
        self.logger.error(f"Failed to fetch from {self.name} after {self.max_retries} attempts")
        return []
        
    def _validate_proxy(self, proxy: str) -> bool:
        """验证代理格式"""
        try:
            # 验证格式: http(s)://ip:port
            pattern = r'^(http|https)://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$'
            if not re.match(pattern, proxy):
                self.logger.debug(f"Invalid proxy format: {proxy}")
                return False
                
            # 验证IP和端口
            protocol, ip_port = proxy.split('://')
            ip, port = ip_port.split(':')
            
            # 验证IP
            ip_parts = [int(p) for p in ip.split('.')]
            if not all(0 <= p <= 255 for p in ip_parts):
                self.logger.debug(f"Invalid IP address: {ip}")
                return False
                
            # 验证端口
            port = int(port)
            if not 1 <= port <= 65535:
                self.logger.debug(f"Invalid port number: {port}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.debug(f"Error validating proxy {proxy}: {e}")
            return False

class IP89Provider(BaseProxyProvider):
    """89免费代理"""
    
    def __init__(self):
        super().__init__('89ip', 'https://www.89ip.cn/tqdl.html?num=100')
    
    async def get_proxies(self) -> List[str]:
        try:
            self.logger.info(f"Fetching proxies from {self.url}")
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        # 使用正则表达式提取IP:PORT
                        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})'
                        matches = re.findall(pattern, text)
                        proxies = [f"http://{ip}:{port}" for ip, port in matches]
                        self.logger.info(f"Got {len(proxies)} proxies from {self.name}")
                        return proxies
                    else:
                        self.logger.warning(f"Failed to fetch from {self.name}: status {response.status}")
        except Exception as e:
            self.logger.warning(f"Error fetching from {self.name}: {e}")
        return []

    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing 89ip content")
        proxies = []
        try:
            # 使用正则表达式提取IP:PORT
            pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})'
            matches = re.findall(pattern, content)
            proxies = [f"http://{ip}:{port}" for ip, port in matches]
            self.logger.debug(f"Found {len(proxies)} proxies")
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
        return proxies

class IP66Provider(BaseProxyProvider):
    """66免费代理"""
    
    def __init__(self):
        super().__init__('66ip', 'http://www.66ip.cn/mo.php?tqsl=100')
    
    async def get_proxies(self) -> List[str]:
        try:
            self.logger.info(f"Fetching proxies from {self.url}")
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})'
                        matches = re.findall(pattern, text)
                        proxies = [f"http://{ip}:{port}" for ip, port in matches]
                        self.logger.info(f"Got {len(proxies)} proxies from {self.name}")
                        return proxies
                    else:
                        self.logger.warning(f"Failed to fetch from {self.name}: status {response.status}")
        except Exception as e:
            self.logger.warning(f"Error fetching from {self.name}: {e}")
        return []

    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing 66ip content")
        proxies = []
        try:
            pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})'
            matches = re.findall(pattern, content)
            proxies = [f"http://{ip}:{port}" for ip, port in matches]
            self.logger.debug(f"Found {len(proxies)} proxies")
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
        return proxies

class KuaidailiProvider(BaseProxyProvider):
    """快代理免费代理"""
    
    def __init__(self):
        super().__init__('kuaidaili', 'https://www.kuaidaili.com/free/inha/')
    
    async def get_proxies(self) -> List[str]:
        try:
            self.logger.info(f"Fetching proxies from {self.url}")
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        soup = BeautifulSoup(text, 'html.parser')
                        proxies = []
                        for tr in soup.find_all('tr')[1:]:
                            tds = tr.find_all('td')
                            if len(tds) >= 2:
                                ip = tds[0].text.strip()
                                port = tds[1].text.strip()
                                proxies.append(f"http://{ip}:{port}")
                        self.logger.info(f"Got {len(proxies)} proxies from {self.name}")
                        return proxies
                    else:
                        self.logger.warning(f"Failed to fetch from {self.name}: status {response.status}")
        except Exception as e:
            self.logger.warning(f"Error fetching from {self.name}: {e}")
        return []

    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing kuaidaili content")
        proxies = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            for tr in soup.find_all('tr')[1:]:
                tds = tr.find_all('td')
                if len(tds) >= 2:
                    ip = tds[0].text.strip()
                    port = tds[1].text.strip()
                    proxies.append(f"http://{ip}:{port}")
            self.logger.debug(f"Found {len(proxies)} proxies")
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
        return proxies

class ProxyListProvider(BaseProxyProvider):
    """proxy-list.download免费代理"""
    
    def __init__(self):
        super().__init__('proxy-list', 'https://www.proxy-list.download/api/v1/get?type=http')
    
    async def get_proxies(self) -> List[str]:
        try:
            self.logger.info(f"Fetching proxies from {self.url}")
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        proxies = [f"http://{line.strip()}" for line in text.split('\n') if line.strip()]
                        self.logger.info(f"Got {len(proxies)} proxies from {self.name}")
                        return proxies
                    else:
                        self.logger.warning(f"Failed to fetch from {self.name}: status {response.status}")
        except Exception as e:
            self.logger.warning(f"Error fetching from {self.name}: {e}")
        return []

    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing proxy-list content")
        proxies = []
        try:
            proxies = [f"http://{line.strip()}" for line in content.split('\n') if line.strip()]
            self.logger.debug(f"Found {len(proxies)} proxies")
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
        return proxies

class ProxyScrapeProvider(BaseProxyProvider):
    """proxyscrape.com免费代理"""
    
    def __init__(self):
        super().__init__('proxyscrape', 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http')
    
    async def get_proxies(self) -> List[str]:
        try:
            self.logger.info(f"Fetching proxies from {self.url}")
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        proxies = [f"http://{line.strip()}" for line in text.split('\n') if line.strip()]
                        self.logger.info(f"Got {len(proxies)} proxies from {self.name}")
                        return proxies
                    else:
                        self.logger.warning(f"Failed to fetch from {self.name}: status {response.status}")
        except Exception as e:
            self.logger.warning(f"Error fetching from {self.name}: {e}")
        return []

    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing proxyscrape content")
        proxies = []
        try:
            proxies = [f"http://{line.strip()}" for line in content.split('\n') if line.strip()]
            self.logger.debug(f"Found {len(proxies)} proxies")
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
        return proxies

class SSLProxiesProvider(BaseProxyProvider):
    """SSLProxies代理提供者"""
    
    def __init__(self):
        super().__init__('sslproxies', 'https://www.sslproxies.org/')
        
    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing SSLProxies content")
        proxies = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            rows = soup.select('table#proxylisttable tbody tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    is_https = cols[6].text.strip() == 'yes'
                    
                    if ip and port:
                        proxy = f"{'https' if is_https else 'http'}://{ip}:{port}"
                        proxies.append(proxy)
                        
            self.logger.debug(f"Found {len(proxies)} proxies")
            
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
            
        return proxies
        
class US_ProxyProvider(BaseProxyProvider):
    """US-Proxy代理提供者"""
    
    def __init__(self):
        super().__init__('us-proxy', 'https://www.us-proxy.org/')
        
    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing US-Proxy content")
        proxies = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            rows = soup.select('table#proxylisttable tbody tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    is_https = cols[6].text.strip() == 'yes'
                    
                    if ip and port:
                        proxy = f"{'https' if is_https else 'http'}://{ip}:{port}"
                        proxies.append(proxy)
                        
            self.logger.debug(f"Found {len(proxies)} proxies")
            
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
            
        return proxies
        
class ProxyListDownloadProvider(BaseProxyProvider):
    """ProxyListDownload代理提供者"""
    
    def __init__(self):
        super().__init__('proxy-list-download', 'https://www.proxy-list.download/api/v1/get?type=http')
        
    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing ProxyListDownload content")
        proxies = []
        try:
            for line in content.splitlines():
                if ':' in line:
                    proxy = f"http://{line.strip()}"
                    proxies.append(proxy)
                    
            self.logger.debug(f"Found {len(proxies)} proxies")
            
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
            
        return proxies
        
class ProxyListPlusProvider(BaseProxyProvider):
    """ProxyListPlus代理提供者"""
    
    def __init__(self):
        super().__init__('proxy-list-plus', 'https://list.proxylistplus.com/Fresh-HTTP-Proxy-List-1')
        
    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing ProxyListPlus content")
        proxies = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            rows = soup.select('table.bg tr')[2:]  # Skip header rows
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    ip = cols[1].text.strip()
                    port = cols[2].text.strip()
                    
                    if ip and port:
                        proxy = f"http://{ip}:{port}"
                        proxies.append(proxy)
                        
            self.logger.debug(f"Found {len(proxies)} proxies")
            
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
            
        return proxies
        
class ProxyDBProvider(BaseProxyProvider):
    """ProxyDB代理提供者"""
    
    def __init__(self):
        super().__init__('proxydb', 'http://proxydb.net/')
        
    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing ProxyDB content")
        proxies = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            rows = soup.select('table tbody tr')
            
            for row in rows:
                data = row.select_one('td:first-child')
                if data:
                    proxy = f"http://{data.text.strip()}"
                    proxies.append(proxy)
                    
            self.logger.debug(f"Found {len(proxies)} proxies")
            
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
            
        return proxies
        
class ProxyDoktorProvider(BaseProxyProvider):
    """ProxyDoktor代理提供者"""
    
    def __init__(self):
        super().__init__('proxydoktor', 'https://www.proxydoktor.com/elite-proxy-list/')
        
    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing ProxyDoktor content")
        proxies = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            rows = soup.select('table.proxy-list tbody tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    
                    if ip and port:
                        proxy = f"http://{ip}:{port}"
                        proxies.append(proxy)
                        
            self.logger.debug(f"Found {len(proxies)} proxies")
            
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
            
        return proxies
        
class ProxyListMeProvider(BaseProxyProvider):
    """ProxyList.me代理提供者"""
    
    def __init__(self):
        super().__init__('proxylist.me', 'https://proxylist.me/')
        
    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing ProxyList.me content")
        proxies = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            rows = soup.select('table.table tbody tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    
                    if ip and port:
                        proxy = f"http://{ip}:{port}"
                        proxies.append(proxy)
                        
            self.logger.debug(f"Found {len(proxies)} proxies")
            
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
            
        return proxies

class ProxyProviderManager:
    """代理提供者管理器"""
    
    def __init__(self):
        self.providers = []  # 代理提供者列表
        self.logger = logger.bind(name="proxy_provider_manager")  # 初始化logger
        
        # 初始化代理提供者
        self.providers.extend([
            IP89Provider(),
            IP66Provider(),
            KuaidailiProvider(),
            ProxyListProvider(),
            ProxyScrapeProvider()
        ])
        self.logger.info(f"Initialized with {len(self.providers)} providers")
        
    async def get_all_proxies(self) -> List[str]:
        """从所有提供者获取代理"""
        self.logger.info("Start fetching proxies from all providers")
        tasks = []
        for provider in self.providers:
            tasks.append(provider.get_proxies())
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        proxies = set()
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Provider {self.providers[i].name} failed: {result}")
                continue
                
            if result:
                proxies.update(result)
                
        self.logger.info(f"Got {len(proxies)} unique proxies from all providers")
        
        # 如果没有获取到代理，使用备用代理
        if not proxies:
            self.logger.warning("No proxies found, using fallback proxies")
            proxies.update([
                "http://127.0.0.1:8080",  # 本地代理
                "http://127.0.0.1:1080",  # 本地代理
                "http://127.0.0.1:7890",  # Clash代理
                "http://127.0.0.1:8888",  # Fiddler代理
                "http://127.0.0.1:8889",  # Burp代理
            ])
            
        return list(proxies)

class FreeProxyListProvider(BaseProxyProvider):
    """FreeProxyList代理提供者"""
    
    def __init__(self):
        super().__init__('free-proxy-list', 'https://free-proxy-list.net/')
        
    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing FreeProxyList content")
        proxies = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            rows = soup.select('table#proxylisttable tbody tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    is_https = cols[6].text.strip() == 'yes'
                    
                    if ip and port:
                        proxy = f"{'https' if is_https else 'http'}://{ip}:{port}"
                        proxies.append(proxy)
                        
            self.logger.debug(f"Found {len(proxies)} proxies")
            
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
            
        return proxies
        
class ProxyNovaProvider(BaseProxyProvider):
    """ProxyNova代理提供者"""
    
    def __init__(self):
        super().__init__('proxynova', 'https://www.proxynova.com/proxy-server-list/')
        
    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing ProxyNova content")
        proxies = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            rows = soup.select('table#tbl_proxy_list tbody tr')
            
            for row in rows:
                script = row.select_one('td:nth-child(1) script')
                port = row.select_one('td:nth-child(2)')
                
                if script and port:
                    # 解析IP地址
                    script_text = script.text
                    ip_match = re.search(r"'([\d\.]+)'", script_text)
                    if ip_match:
                        ip = ip_match.group(1)
                        port = port.text.strip()
                        if ip and port:
                            proxy = f"http://{ip}:{port}"
                            proxies.append(proxy)
                            
            self.logger.debug(f"Found {len(proxies)} proxies")
            
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
            
        return proxies
        
class SpysOneProvider(BaseProxyProvider):
    """Spys.one代理提供者"""
    
    def __init__(self):
        super().__init__('spys.one', 'http://spys.one/free-proxy-list/ALL/')
        
    async def parse(self, content: str) -> List[str]:
        self.logger.debug("Parsing Spys.one content")
        proxies = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            rows = soup.select('tr[onmouseover]')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    ip_port = cols[0].text.strip()
                    if ':' in ip_port:
                        proxy = f"http://{ip_port}"
                        proxies.append(proxy)
                        
            self.logger.debug(f"Found {len(proxies)} proxies")
            
        except Exception as e:
            self.logger.error(f"Error parsing content: {e}")
            
        return proxies

async def test_providers():
    """测试所有代理源"""
    manager = ProxyProviderManager()
    proxies = await manager.get_all_proxies()
    logger.info(f"Total proxies: {len(proxies)}")
    for proxy in proxies[:5]:  # 只显示前5个代理
        logger.info(f"Sample proxy: {proxy}")

if __name__ == "__main__":
    asyncio.run(test_providers()) 