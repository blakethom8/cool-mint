import axios from 'axios';
import { 
  Bundle, 
  BundleListResponse, 
  BundleDetailResponse, 
  BundleStatsResponse, 
  ActivitySelectionResponse,
  BundleDeleteResponse 
} from '../types/bundle';

const API_BASE_URL = '';

export const bundleService = {
  // Get bundle statistics before creation
  async getBundleStats(activityIds: string[]): Promise<BundleStatsResponse> {
    const response = await axios.post(`/activities/selection/stats`, {
      activity_ids: activityIds,
    });
    return response.data;
  },

  // Create a bundle from selected activities
  async createBundle(
    activityIds: string[],
    bundleName: string,
    bundleDescription?: string
  ): Promise<ActivitySelectionResponse> {
    const response = await axios.post(`/activities/selection`, {
      activity_ids: activityIds,
      bundle_name: bundleName,
      bundle_description: bundleDescription,
    });
    return response.data;
  },

  // List all bundles
  async listBundles(
    page: number = 1,
    pageSize: number = 50,
    search?: string,
    sortBy: string = 'created_at',
    sortOrder: string = 'desc'
  ): Promise<BundleListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      sort_by: sortBy,
      sort_order: sortOrder,
    });

    if (search) {
      params.append('search', search);
    }

    const response = await axios.get(`/api/bundles?${params}`);
    return response.data;
  },

  // Get bundle details
  async getBundleDetail(bundleId: string): Promise<BundleDetailResponse> {
    const response = await axios.get(`/api/bundles/${bundleId}`);
    return response.data;
  },

  // Delete a bundle
  async deleteBundle(bundleId: string): Promise<BundleDeleteResponse> {
    const response = await axios.delete(`/api/bundles/${bundleId}`);
    return response.data;
  },
};