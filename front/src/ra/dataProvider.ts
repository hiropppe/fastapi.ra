import { fetchUtils, HttpError, Identifier } from 'react-admin';
import { stringify } from "query-string";

const API_URL = import.meta.env.VITE_DATA_PROVIDER_URL;
const READ_API_URL = import.meta.env.VITE_READ_DATA_PROVIDER_URL;

const baseDataProvider = {
  // @ts-ignore
  getList: (resource, params) => {
    const { page, perPage } = params.pagination;
    const { field, order } = params.sort;
  
    const query = {
      sort: JSON.stringify([field, order]),
      range: JSON.stringify([(page - 1) * perPage, page * perPage - 1]),
      filter: JSON.stringify(params.filter),
    };
    
    // metaパラメータがある場合、追加のクエリパラメータとして展開
    if (params.meta) {
      Object.keys(params.meta).forEach(key => {
        query[key] = params.meta[key];
      });
    }
    
    const url = `${READ_API_URL ? READ_API_URL: API_URL}/${resource}?${stringify(query)}`;
  
    return fetchUtils.fetchJson(url, {
      method: "GET",
      headers: new Headers({
        "accept": "application/json"
      }),
      credentials: 'include'
    }).then(({ headers, json }) => ({
      data: json["data"],
      total: parseInt(headers.get('content-range')!.split('/').pop()!, 10),
    }));
  },
  // @ts-ignore
  getOne: (resource, params) => {
    const url = `${READ_API_URL ? READ_API_URL: API_URL}/${resource}/${params.id}`;

    return fetchUtils.fetchJson(url, {
      method: "GET",
      headers: new Headers({
        "accept": "application/json"
      }),
      credentials: 'include'
    }).then(({ headers, json }) => ({
      data: "data" in json ? json["data"] : json,
    }));
  },
  // @ts-ignore
  getMany: (resource, params) => {
    const query = {
      sort: '[]',
      range: '[]',
      filter: JSON.stringify({ id: params.ids }),
    };
    const url = `${READ_API_URL ? READ_API_URL: API_URL}/${resource}?${stringify(query)}`;
    
    return fetchUtils.fetchJson(url, {
      method: "GET",
      headers: new Headers({
        "accept": "application/json"
      }),
      credentials: 'include'
    }).then(({ headers, json }) => ({
      data: json["data"] || [],
    })).catch(error => {
      console.error(`getMany error for ${resource}:`, error);
      return Promise.reject(new HttpError('getMany failed', 500, error));
    });
  },
  // @ts-ignore
  getManyReference: (resource, params) => {
  },
  // @ts-ignore
  create: (resource, params) => {
    const url = `${API_URL}/${resource}`;
  
    return fetchUtils.fetchJson(url, {
      method: "POST",
      headers: new Headers({
        "accept": "application/json"
      }),
      body: JSON.stringify(params["data"]),
      credentials: 'include'
    }).then(({ headers, json }) => ({
      data: json.data,
    }));
  },
  // @ts-ignore
  update: (resource, params) => {
    const url = `${API_URL}/${resource}/${params.id}`;

    return fetchUtils.fetchJson(url, {
      method: "POST",
      headers: new Headers({
        "accept": "application/json"
      }),
      body: JSON.stringify(params.data),
      credentials: 'include'
    }).then(({ headers, json }) => ({
      data: "data" in json ? json["data"] : json,
    }));
  },
  // @ts-ignore
  updateMany: (resource, params) => {
    const url = `${API_URL}/${resource}`;

    return fetchUtils.fetchJson(url, {
      method: "POST",
      headers: new Headers({
        "accept": "application/json"
      }),
      body: JSON.stringify(params),
      credentials: 'include'
    }).then(({ headers, json }) => ({
      data: json.data,
    }));
  },
  // @ts-ignore
  delete: (resource, params) => {
    const url = `${API_URL}/${resource}/${params.id}`;

    return fetchUtils.fetchJson(url, {
      method: "DELETE",
      headers: new Headers({
        "accept": "application/json"
      }),
      body: JSON.stringify(params.data),
      credentials: 'include'
    }).then(({ headers, json }) => ({
      data: "data" in json ? json["data"] : json,
    }));
  },
  // @ts-ignore
  deleteMany: (resource, params) => {
  },
}

const getExcelUploadForm = (params: { file: string | Blob; }) => {
  const formData = new FormData();
  formData.append("upload_file", params.file);
  return formData;
};

export const dataProvider = {
  ...baseDataProvider,

  // @ts-ignore
  count: (resource, params) => {
    const query = {
      filter: JSON.stringify(params.filter),
      groupby: params.groupby,
    };
  
    const url = `${READ_API_URL ? READ_API_URL: API_URL}/${resource}/_count?${stringify(query)}`;

    return fetchUtils.fetchJson(url, {
      method: "GET",
      headers: new Headers({
        "accept": "application/json"
      }),
      credentials: 'include'
    }).then(({ headers, json }) => ({
      data: json
    }));
  },
  
  // https://stackoverflow.com/questions/71313129/how-to-render-streamable-image-on-react-coming-from-fastapi-server
  // https://stackoverflow.com/questions/60655151/download-file-from-data-of-an-api-response-with-react-admin
  // @ts-ignore  
  downloadExcel: (resource, params) => {
    const { field, order } = params.sort;
  
    const query = {
      sort: JSON.stringify([field, order]),
      filter: JSON.stringify(params.filter),
    };
    const url = `${READ_API_URL ? READ_API_URL: API_URL}/${resource}.xlsx?${stringify(query)}`;
    let filename: string;

    return fetch(url, {
      method: "GET",
      headers: new Headers({
        "accept": "application/json"
      }),
      credentials: 'include'
    })
    .then(response => {
      const contentDisposition = response.headers.get('Content-Disposition');
      const filenameMatch = contentDisposition!.match(/filename="(.+?)"/);
      filename = filenameMatch!.at(1)!;
      return response.blob()
    })
    .then(blob => {
      // Creating the hyperlink and auto click it to start the download      
      let url = URL.createObjectURL(blob);
      let link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.click();
    });
  },
  // @ts-ignore
  uploadExcel: (resource, params) => {
    const formData = getExcelUploadForm(params);
    const url = `${API_URL}/${resource}.xlsx`;

    return fetchUtils
      .fetchJson(url, {
        method: "POST",
        headers: new Headers({
          "accept": "application/json"
        }),
        body: formData,
        credentials: 'include'
      })
      .then(({ status, body, json }) => {
        if (status < 200 || status >= 300) {
          throw new HttpError(
              (json && json.message) || status,
              status,
              body
          );
        }
        return json;
      });
  },

  // @ts-ignore
  uploadSharedReport: (resource, params) => {
    const formData = getExcelUploadForm(params);
    const url = `${API_URL}/${resource}`;

    return fetchUtils
      .fetchJson(url, {
        method: "POST",
        headers: new Headers({
          "accept": "application/json"
        }),
        body: formData,
        credentials: 'include'
      })
      .then(({ status, body, json }) => {
        if (status < 200 || status >= 300) {
          throw new HttpError(
              (json && json.message) || status,
              status,
              body
          );
        }
        return json;
      });
  },

  // @ts-ignore
  downloadFile: (resource) => {
    const url = `${READ_API_URL ? READ_API_URL: API_URL}/${resource}`;
    let filename: string;

    return fetch(url, {
      method: "GET",
      headers: new Headers({
        "accept": "text/csv"
      }),
      credentials: 'include'
    })
    .then(response => {
      const contentDisposition = response.headers.get('Content-Disposition');
      const filenameMatch = contentDisposition!.match(/filename="(.+?)"/);
      filename = filenameMatch!.at(1)!;
      return response.blob()
    })
    .then(blob => {
      // Creating the hyperlink and auto click it to start the download
      let url = URL.createObjectURL(blob);
      let link = document.createElement('a');
      link.href = url;
      link.download = decodeURI(filename);
      link.click();
    });
  },


  downloadCSV: (resource, params) => {
    const { field, order } = params.sort;

    const query = {
      sort: JSON.stringify([field, order]),
      filter: JSON.stringify(params.filter),
    };
    const url = `${READ_API_URL ? READ_API_URL: API_URL}/${resource}.csv?${stringify(query)}`;
    let filename: string;

    return fetch(url, {
      method: "GET",
      headers: new Headers({
        //"Authorization": authorization,
        "accept": "text/csv"
      }),
      credentials: 'include'
    })
    .then(response => {
      const contentDisposition = response.headers.get('Content-Disposition');
      const filenameMatch = contentDisposition!.match(/filename="(.+?)"/);
      filename = filenameMatch!.at(1)!;
      return response.blob()
    })
    .then(blob => {
      // Creating the hyperlink and auto click it to start the download
      let url = URL.createObjectURL(blob);
      let link = document.createElement('a');
      link.href = url;
      link.download = decodeURI(filename);
      link.click();
    });
  },
}
