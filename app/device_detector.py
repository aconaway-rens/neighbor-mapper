"""
Device Type Detector
Uses YAML configuration to map CDP/LLDP platform info to Netmiko device types
"""

import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class DeviceTypeDetector:
    """Detect Netmiko device types from CDP/LLDP platform information"""
    
    def __init__(self, config_path: str = "config/device_type_patterns.yaml"):
        self.config_path = Path(config_path)
        self.patterns = self._load_patterns()
        self.default_type = self.patterns.get('default_device_type', 'cisco_ios')
        # Ensure all capabilities are strings
        self.allowed_capabilities = set(str(c) for c in self.patterns.get('allowed_capabilities', []))
        logger.info(f"Device type detector initialized with {len(self.patterns.get('device_types', {}))} device types")
    
    def _load_patterns(self) -> Dict:
        """Load patterns from YAML configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded device type patterns from {self.config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_patterns()
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            return self._get_default_patterns()
    
    def detect_from_cdp(self, platform: str, capabilities: str = "", filters: dict = None) -> Optional[str]:
        """
        Detect device type from CDP platform and capabilities
        
        Args:
            platform: CDP platform string (e.g., "cisco WS-C3750X-48")
            capabilities: CDP capabilities (e.g., "Router Switch IGMP")
            filters: Device type filters (include_routers, include_switches, etc.)
            
        Returns:
            Netmiko device type string or None if no match found
        """
        device_type = self._match_patterns(platform, "")
        logger.debug(f"CDP platform '{platform}' detected as '{device_type}'")
        return device_type
    
    def detect_from_lldp(self, system_desc: str, capabilities: str = "", filters: dict = None) -> Optional[str]:
        """
        Detect device type from LLDP system description
        
        Args:
            system_desc: LLDP system description
            capabilities: LLDP system capabilities
            filters: Device type filters (include_routers, include_switches, etc.)
            
        Returns:
            Netmiko device type string or None if no match found
        """
        device_type = self._match_patterns("", system_desc)
        logger.debug(f"LLDP description detected as '{device_type}'")
        return device_type
    
    def _should_crawl(self, capabilities: str, filters: dict = None) -> bool:
        """
        Determine if we should crawl this device based on capabilities and filters
        
        Args:
            capabilities: Comma or space-separated capabilities string
            filters: Dict of device type filters (include_routers, include_switches, etc.)
            
        Returns:
            True if device should be crawled based on filters
        """
        if not capabilities:
            # If no capabilities, assume it's crawlable (default to router/switch)
            if filters is None:
                return True
            return filters.get('include_routers', True) or filters.get('include_switches', True)
        
        # Parse capabilities (could be "Router Switch" or "R,S" format)
        caps = set(str(capabilities).replace(',', ' ').upper().split())
        
        # If no filters provided, use old behavior (routers and switches only)
        if filters is None:
            return bool(caps & {str(c).upper() for c in self.allowed_capabilities})
        
        # Check each device type based on capabilities
        device_category, _ = self._categorize_device(caps, platform="", system_desc="")
        
        # Return based on filter settings
        if device_category == 'router':
            return filters.get('include_routers', False)
        elif device_category == 'firewall':
            # Firewalls are crawlable like routers
            return filters.get('include_routers', False)
        elif device_category == 'switch':
            return filters.get('include_switches', False)
        elif device_category == 'phone':
            return filters.get('include_phones', False)
        elif device_category == 'server':
            return filters.get('include_servers', False)
        elif device_category == 'access_point':
            return filters.get('include_aps', False)
        else:
            return filters.get('include_other', False)
    
    def _categorize_device(self, caps: set, platform: str = "", system_desc: str = "") -> tuple:
        """
        Categorize device based on capabilities, platform, and system description
        
        Args:
            caps: Set of capability strings (uppercase)
            platform: Platform string for additional detection (e.g., "Palo Alto Networks PA-3220")
            system_desc: System description (LLDP) for additional detection
            
        Returns:
            Tuple of (category, has_routing) where:
            - category: 'router', 'switch', 'phone', 'server', 'access_point', 'firewall', or 'other'
            - has_routing: Boolean indicating if device has Router capability
        """
        has_routing = any(c in caps for c in ['ROUTER', 'R'])
        
        # Platform-based detection for firewalls (check FIRST before capability-based)
        # Firewalls typically report "Router" capability but we can detect them by platform or system description
        firewall_keywords = ['palo alto', 'paloalto', 'fortinet', 'fortigate', 'checkpoint', 
                            'cisco asa', 'firepower', 'sophos', 'sonicwall', 'watchguard',
                            'barracuda', 'juniper srx', 'pa-', 'fw-', 'pan-os']
        
        # Check both platform and system_desc (LLDP uses system_desc for platform info)
        text_to_check = (platform + " " + system_desc).lower()
        if any(keyword in text_to_check for keyword in firewall_keywords):
            return ('firewall', has_routing)
        
        # Access Point detection (check BEFORE bridge, since Trans-Bridge = AP)
        if any(c in caps for c in ['WLAN', 'W', 'AP']):
            return ('access_point', has_routing)
        
        # Check for Trans-Bridge (Cisco APs report as this)
        if 'TRANS-BRIDGE' in caps:
            return ('access_point', has_routing)
        
        # Phone detection
        if any(c in caps for c in ['PHONE', 'P', 'T']):  # T = telephone
            return ('phone', has_routing)
        
        # Server/Host detection
        if any(c in caps for c in ['HOST', 'H', 'SERVER']):
            return ('server', has_routing)
        
        # Switch/Bridge detection - CHECK THIS BEFORE ROUTER
        # Many switches report both "Router Switch" but should be categorized as switches
        if any(c in caps for c in ['SWITCH', 'S', 'BRIDGE', 'B']):
            return ('switch', has_routing)
        
        # Router detection - AFTER switch check
        if has_routing:
            return ('router', has_routing)
        
        # Default to other
        return ('other', has_routing)
    
    def _match_patterns(self, platform: str, system_desc: str) -> str:
        """
        Match platform/description against configured patterns
        
        Args:
            platform: Platform string to match
            system_desc: System description to match
            
        Returns:
            Best matching device type
        """
        platform_lower = str(platform).lower()
        desc_lower = str(system_desc).lower()
        
        matches = []
        
        for device_type, config in self.patterns.get('device_types', {}).items():
            score = 0
            
            # Check platform patterns
            for pattern in config.get('platforms', []):
                if str(pattern).lower() in platform_lower:
                    score += config.get('priority', 10)
                    logger.debug(f"Platform pattern '{pattern}' matched for {device_type}")
                    break
            
            # Check system description patterns
            for pattern in config.get('system_descriptions', []):
                if str(pattern).lower() in desc_lower:
                    score += config.get('priority', 10) * 0.5
                    logger.debug(f"Description pattern '{pattern}' matched for {device_type}")
                    break
            
            if score > 0:
                matches.append((device_type, score))
        
        if matches:
            # Return highest scoring match
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[0][0]
        
        logger.debug(f"No pattern matched, using default: {self.default_type}")
        return self.default_type
    
    def reload_config(self):
        """Reload patterns from configuration file"""
        self.patterns = self._load_patterns()
        self.default_type = self.patterns.get('default_device_type', 'cisco_ios')
        logger.info("Configuration reloaded")
    
    def _get_default_patterns(self) -> Dict:
        """Return minimal default patterns if config file is missing"""
        return {
            'device_types': {
                'cisco_ios': {
                    'platforms': ['cisco', 'catalyst'],
                    'system_descriptions': ['IOS'],
                    'priority': 50
                }
            },
            'allowed_capabilities': ['Router', 'Switch', 'R', 'S', 'B'],
            'default_device_type': 'cisco_ios'
        }
