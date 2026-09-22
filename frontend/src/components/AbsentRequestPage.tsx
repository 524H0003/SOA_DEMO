import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listAbsentRequests, createAbsentRequest } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

interface AbsentRequest {
  id: number;
  employee_name: string;
  employee_email: string;
  manager_email: string;
  absent_type: string;
  start_date: string;
  end_date: string;
  reason: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
  decided_at: string | null;
}

interface AbsentRequestFormData {
  absent_type: string;
  start_date: string;
  end_date: string;
  reason: string;
}

export function AbsentRequestPage() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState<AbsentRequestFormData>({
    absent_type: "Annual",
    start_date: "",
    end_date: "",
    reason: "",
  });

  const { data: requests = [], isLoading } = useQuery({
    queryKey: ["absentRequests"],
    queryFn: listAbsentRequests,
  });

  const createRequestMutation = useMutation({
    mutationFn: createAbsentRequest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["absentRequests"] });
      setIsDialogOpen(false);
      setFormData({
        absent_type: "Annual",
        start_date: "",
        end_date: "",
        reason: "",
      });
    },
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (value: string) => {
    setFormData((prev) => ({ ...prev, absent_type: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createRequestMutation.mutate(formData);
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Absent Requests</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">
            Logged in as: {user?.username}
          </span>
          <Button variant="outline" size="sm" onClick={handleLogout}>
            Logout
          </Button>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>New Request</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Create Absent Request</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="absent_type">Absent Type</Label>
                  <Select
                    value={formData.absent_type}
                    onValueChange={handleSelectChange}
                  >
                    <SelectTrigger id="absent_type">
                      <SelectValue placeholder="Select absent type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Annual">Annual</SelectItem>
                      <SelectItem value="Sick">Sick</SelectItem>
                      <SelectItem value="Personal">Personal</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="start_date">Start Date</Label>
                  <Input
                    id="start_date"
                    name="start_date"
                    type="date"
                    value={formData.start_date}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="end_date">End Date</Label>
                  <Input
                    id="end_date"
                    name="end_date"
                    type="date"
                    value={formData.end_date}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reason">Reason</Label>
                  <Textarea
                    id="reason"
                    name="reason"
                    value={formData.reason}
                    onChange={handleChange}
                    required
                    placeholder="Enter the reason for your absence..."
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={createRequestMutation.isPending}
                >
                  {createRequestMutation.isPending
                    ? "Submitting..."
                    : "Submit Request"}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your Absent Requests</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div>Loading requests...</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Dates</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((request: AbsentRequest) => (
                  <TableRow key={request.id}>
                    <TableCell>
                      AR-{request.id.toString().padStart(3, "0")}
                    </TableCell>
                    <TableCell>{request.absent_type}</TableCell>
                    <TableCell>
                      {request.start_date} → {request.end_date}
                    </TableCell>
                    <TableCell>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          request.status === "approved"
                            ? "bg-green-100 text-green-800"
                            : request.status === "rejected"
                              ? "bg-red-100 text-red-800"
                              : "bg-yellow-100 text-yellow-800"
                        }`}
                      >
                        {request.status.charAt(0).toUpperCase() +
                          request.status.slice(1)}
                      </span>
                    </TableCell>
                    <TableCell>
                      {new Date(request.created_at).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
