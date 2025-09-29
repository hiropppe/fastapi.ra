import React, { useState, useEffect } from 'react';
import AddIcon from '@mui/icons-material/Add';
import {
    List,
    TopToolbar,
    SelectColumnsButton,
    FilterButton,
    useAuthenticated,
    Pagination,
} from 'react-admin';

import { Box } from '@mui/material';

import UserRow from './Row'


const UserList = () => {

    useAuthenticated();

    const [filterValues, setFilterValues] = useState({
        username: null as any,
    });

    const Actions = () => {
        return (
            <TopToolbar>
                <SelectColumnsButton />
            </TopToolbar>
        )
    }

    const Row = () => {
        return (
            <UserRow />
        )
    }

    return (
        <Box display="flex">
            <List
                resource="users"
                actions={<Actions />}
                sort={{ field: 'id', order: 'DESC'}}
                pagination={<Pagination rowsPerPageOptions={[10, 25, 50, 100]} />}
                perPage={25}>
                <Row />
            </List>
        </Box>
    );
};

export default UserList;
