import os
import sys
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()
RAILWAY_TOKEN = os.getenv('RAILWAY_TOKEN')
BASE_URL = 'https://backboard.railway.com/graphql/v2'

HEADERS = {
    'Authorization': f'Bearer {RAILWAY_TOKEN}' if RAILWAY_TOKEN else '',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}


def graphql(query, variables=None):
    if not RAILWAY_TOKEN:
        raise ValueError('RAILWAY_TOKEN is not set in .env')

    payload = {'query': query}
    if variables is not None:
        payload['variables'] = variables

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(BASE_URL, data=data, headers=HEADERS, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')
        raise RuntimeError(f'HTTP {e.code} {e.reason}: {body}')
    except urllib.error.URLError as e:
        raise RuntimeError(f'Connection error: {e}')


def print_json(data):
    print(json.dumps(data, indent=2, sort_keys=True))


def get_status():
    query = 'query { me { id name email } }'
    result = graphql(query)
    if 'errors' in result:
        print_json(result)
        return
    print('Railway token is valid. User info:')
    print_json(result['data']['me'])


def list_projects():
    query = 'query { projects { edges { node { id name } } } }'
    result = graphql(query)
    if 'errors' in result:
        print_json(result)
        return
    projects = result['data']['projects']['edges']
    if not projects:
        print('No projects found for this Railway account.')
        return
    print('Railway projects:')
    for edge in projects:
        node = edge['node']
        print(f"- {node['name']} ({node['id']})")


def show_project(project_id):
    query = '''
    query Project($id: String!) {
      project(id: $id) {
        id
        name
        description
        workspace { id name }
        services { edges { node { id name } } }
        environments { edges { node { id name } } }
      }
    }
    '''
    result = graphql(query, {'id': project_id})
    if 'errors' in result:
        print_json(result)
        return
    print_json(result['data']['project'])


def show_service(service_id):
    query = '''
    query Service($id: String!) {
      service(id: $id) {
        id
        name
        createdAt
        updatedAt
      }
    }
    '''
    result = graphql(query, {'id': service_id})
    if 'errors' in result:
        print_json(result)
        return
    print_json(result['data']['service'])


def usage():
    print('Usage: python railway_connect.py <command>')
    print('Commands:')
    print('  status                Check Railway token and current user')
    print('  projects              List Railway projects')
    print('  project <project-id>  Show details for a Railway project')
    print('  service <service-id>  Show details for a Railway service')
    print('  help                  Show this help message')


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in ('help', '-h', '--help'):
        usage()
        sys.exit(0)

    command = sys.argv[1]
    try:
        if command == 'status':
            get_status()
        elif command == 'projects':
            list_projects()
        elif command == 'project':
            if len(sys.argv) != 3:
                print('project command requires a project ID')
                usage()
                sys.exit(1)
            show_project(sys.argv[2])
        elif command == 'service':
            if len(sys.argv) != 3:
                print('service command requires a service ID')
                usage()
                sys.exit(1)
            show_service(sys.argv[2])
        else:
            print(f'Unknown command: {command}')
            usage()
            sys.exit(1)
    except Exception as ex:
        print(f'Error: {ex}')
        sys.exit(1)
