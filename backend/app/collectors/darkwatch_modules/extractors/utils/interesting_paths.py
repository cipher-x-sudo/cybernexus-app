

from typing import List, Set


# Common interesting paths to check
INTERESTING_PATHS = [
    '/admin',
    '/administrator',
    '/wp-admin',
    '/wp-login.php',
    '/phpmyadmin',
    '/.git',
    '/.svn',
    '/.env',
    '/config.php',
    '/backup',
    '/backups',
    '/test',
    '/debug',
    '/api',
    '/api/v1',
    '/graphql',
    '/swagger',
    '/phpinfo.php',
    '/info.php',
    '/.well-known',
    '/robots.txt',
    '/sitemap.xml',
    '/.htaccess',
    '/.htpasswd',
    '/login',
    '/signin',
    '/register',
    '/signup',
    '/dashboard',
    '/panel',
    '/cpanel',
    '/phpmyadmin',
    '/mysql',
    '/database',
    '/db',
    '/sql',
    '/upload',
    '/uploads',
    '/files',
    '/download',
    '/downloads',
]


def get_interesting_paths() -> List[str]:
    
    return INTERESTING_PATHS.copy()


def find_interesting_paths_in_content(content: str, base_url: str) -> Set[str]:
    
    found_paths = set()
    content_lower = content.lower()
    
    for path in INTERESTING_PATHS:
        if path.lower() in content_lower:
            found_paths.add(f"{base_url.rstrip('/')}{path}")
    
    return found_paths
