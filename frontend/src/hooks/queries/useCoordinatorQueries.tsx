import { useQuery } from "@tanstack/react-query";
import api from '@/lib/axios'

const fetchColleges=async()=>{
    const {data} = await api.get('/api/coordinator/colleges')
    return data
}

const fetchCollegeDetails = async(collegeId:string,page:number,sortBy:string,statusFilter:string,searchQuery:string)=>{
    const {data} = await api.get(`/api/coordinator/colleges/${collegeId}?page=${page}&limit=10&sort=${sortBy}&status=${statusFilter}&search=${searchQuery}`)
    return data
}

const fetchCollegeAnalytics = async(collegeId:string)=>{
    const {data} = await api.get(`/api/coordinator/colleges/${collegeId}/analytics`)
    return data
}


export function useCoordinatorColleges(){
    return useQuery({
        queryKey:['coordinator','colleges'],
        queryFn:fetchColleges
    })
}

export function useCoordinatorCollegeDetails(
    collegeId:string|null,
    page:number,
    sortBy:string,
    statusFilter:string,
    searchQuery:string
){
    return useQuery({
        queryKey:['coordinator','college-details',collegeId,page,sortBy,statusFilter,searchQuery],
        queryFn:()=>fetchCollegeDetails(collegeId!,page,sortBy,statusFilter,searchQuery),
        enabled:!!collegeId
    })
}

export function useCoordinatorCollegeAnalytics(
    collegeId:string|null
){
    return useQuery({
        queryKey:['coordinator','college-analytics',collegeId],
        queryFn:()=>fetchCollegeAnalytics(collegeId!),
        enabled:!!collegeId
    })
}
