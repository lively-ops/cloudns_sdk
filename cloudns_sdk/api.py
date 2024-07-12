import requests
from .rate_limit import rate_limited
from .exceptions import ClouDNSAPIException
from .validations import validate

class ClouDNSAPI:
    BASE_URL = "https://api.cloudns.net"
    RATE_LIMIT_PER_SECOND = 20

    def __init__(self, auth_id=None, auth_password=None):
        self.auth_id = auth_id
        self.auth_password = auth_password

    @rate_limited(RATE_LIMIT_PER_SECOND)
    def make_request(self, endpoint, method='GET', params=None, data=None):
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        if method == 'GET':
            response = requests.get(url, params=params)
        elif method == 'POST':
            response = requests.post(url, data=data or {})
        else:
            raise ValueError("Unsupported HTTP method")

        if response.status_code != 200:
            raise ClouDNSAPIException(response.json())

        return response.json()

    def _auth_params(self, additional_params=None):
        params = {
            'auth-id': self.auth_id,
            'auth-password': self.auth_password,
        }
        if additional_params:
            params.update(additional_params)
        return params

    def login(self):
        params = {
            'auth-id': self.auth_id,
            'auth-password': self.auth_password
        }
        return self.make_request('login/login.json', method='POST', data=params)

    def get_current_ip(self):
        return self.make_request('ip/get-my-ip.json', method='GET', params=self._auth_params())

    def get_account_balance(self):
        return self.make_request('account/get-balance.json', method='GET', params=self._auth_params())

    def get_available_name_servers(self, detailed_info=0):
        params = self._auth_params({'detailed-info': detailed_info})
        return self.make_request('dns/available-name-servers.json', method='GET', params=params)

    def register_domain_zone(self, domain_name, zone_type, ns=None, master_ip=None):
        params = [
            ('auth-id', self.auth_id),
            ('auth-password', self.auth_password),
            ('domain-name', domain_name),
            ('zone-type', zone_type)
        ]

        if ns:
            for ns_server in ns:
                params.append(('ns[]', ns_server))

        if master_ip:
            params.append(('master-ip', master_ip))

        return self.make_request('dns/register.json', method='POST', params=params)

    def delete_domain_zone(self, domain_name):
        params = {
            'auth-id': self.auth_id,
            'auth-password': self.auth_password,
            'domain-name': domain_name
        }
        return self.make_request('dns/delete.json', method='POST', params=params)

    def list_zones(self, page=1, rows_per_page=20, search=None, group_id=None, has_cloud_domains=None):
        params = self._auth_params({
            'page': page,
            'rows-per-page': rows_per_page,
            'search': search,
            'group-id': group_id,
            'has-cloud-domains': has_cloud_domains
        })
        return self.make_request('dns/list-zones.json', method='GET', params=params)

    def get_pages_count(self, rows_per_page=10, search=None, group_id=None, has_cloud_domains=None):
        params = self._auth_params({
            'rows-per-page': rows_per_page,
            'search': search,
            'group-id': group_id,
            'has-cloud-domains': has_cloud_domains
        })
        return self.make_request('dns/get-pages-count.json', method='GET', params=params)

    def get_zones_stats(self):
        return self.make_request('dns/get-zones-stats.json', method='GET', params=self._auth_params())

    def get_zone_info(self, domain_name):
        params = self._auth_params({'domain-name': domain_name})
        return self.make_request('dns/get-zone-info.json', method='GET', params=params)

    def update_zone(self, domain_name):
        params = self._auth_params({'domain-name': domain_name})
        return self.make_request('dns/update-zone.json', method='POST', params=params)

    def get_update_status(self, domain_name):
        params = self._auth_params({'domain-name': domain_name})
        return self.make_request('dns/update-status.json', method='GET', params=params)

    def is_updated(self, domain_name):
        params = self._auth_params({'domain-name': domain_name})
        return self.make_request('dns/is-updated.json', method='GET', params=params)

    def change_zone_status(self, domain_name, status=None):
        params = self._auth_params({'domain-name': domain_name, 'status': status})
        return self.make_request('dns/change-status.json', method='POST', params=params)

    def get_records_stats(self):
        return self.make_request('dns/get-records-stats.json', method='GET', params=self._auth_params())

    def get_record(self, domain_name, record_id):
        params = self._auth_params({'domain-name': domain_name, 'record-id': record_id})
        return self.make_request('dns/get-record.json', method='GET', params=params)

    def list_records(self, domain_name, host=None, host_like=None, record_type=None,
                     rows_per_page=20, page=1, order_by=None):
        params = self._auth_params({
            'domain-name': domain_name,
            'host': host,
            'host-like': host_like,
            'type': record_type,
            'rows-per-page': rows_per_page,
            'page': page,
            'order-by': order_by
        })
        return self.make_request('dns/records.json', method='GET', params=params)

    def get_records_pages_count(self, domain_name, host=None, record_type=None, rows_per_page=20):
        params = self._auth_params({
            'domain-name': domain_name,
            'host': host,
            'type': record_type,
            'rows-per-page': rows_per_page
        })
        return self.make_request('dns/get-records-pages-count.json', method='GET', params=params)

    def add_record(self, domain_name, record_type, record=None, host='', ttl=3600, **kwargs):
        record_data = {key: value for key, value in locals().items() if key != 'kwargs' and value is not None}
        record_data.update(kwargs)

        valid, error = validate(record_data)

        if valid:
            params = self._auth_params({record_data})
            return self.make_request('dns/add-record.json', method='POST', data=params)
        else:
            raise ValueError(f"Error: {error}")

    def delete_record(self, domain_name, record_id):
        params = self._auth_params({
            'domain-name': domain_name,
            'record-id': record_id
        })
        return self.make_request('dns/delete-record.json', method='POST', params=params)

    def modify_record(self, domain_name, record_id, host='', record=None, ttl=3600, **kwargs):

        record_data = {key: value for key, value in locals().items() if key != 'kwargs' and value is not None}
        record_data.update(kwargs)

        valid, error = validate(record_data)

        if valid:
            params = self._auth_params({record_data})
            return self.make_request('dns/mod-record.json', method='POST', data=params)
        else:
            raise ValueError(f"Error: {error}")

    def copy_records(self, domain_name, from_domain, delete_current_records=False):
        params = self._auth_params({
            'domain-name': domain_name,
            'from-domain': from_domain,
            'delete-current-records': 1 if delete_current_records else 0
        })

        return self.make_request('dns/copy-records.json', method='POST', params=params)


    def import_records(self, domain_name, format='bind', content='', delete_exisiting_records=False, record_types=None):
        params = [
            ('auth-id', self.auth_id),
            ('auth-password', self.auth_password),
            ('domain-name', domain_name),
            ('format', format),
            ('content', content)
        ]

        if record_types:
            for type in record_types:
                params.append(('record-types[]', type))

        if delete_exisiting_records:
            params.append(('delete-existing-records', 1))
        else:
            params.append(('delete-existing-records', 0))

        return self.make_request('dns/records-import.json', method='POST', params=params)

